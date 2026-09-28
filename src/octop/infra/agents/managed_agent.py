"""Provisioning rules for system-managed agents."""

from __future__ import annotations

import json
from importlib import resources
from pathlib import Path
from typing import Any

from octop.infra.agents.default_agent import default_home_local_backend
from octop.infra.agents.experts.catalog import build_create_spec_from_expert
from octop.infra.agents.managed_runtime import MANAGED_ZDX_TYPE

ZDX_PROVIDER_NAME = "tonglian-zdx"  # Legacy identifier retained for cleanup only.
ZDX_PROVIDER_LABEL = "通联智多星"
ZDX_PROVIDER_BASE_URL = "https://ai.allinpay.com/v1/"
ZDX_MODEL_ID = "auto"

ZDX_EXPERT_ID = "tonglian-fazai"
ZDX_TEMPLATE_VERSION = "7"
ZDX_ICON_URL = "/experts/avatars/tonglian-fazai.png"


def zdx_template_dir() -> Path:
    return Path(__file__).resolve().parent / "experts" / "library" / "tonglian-fazai"


def list_builtin_skill_slugs() -> list[str]:
    root = resources.files("octop.infra.agents.builtin_skills")
    return sorted(
        entry.name
        for entry in root.iterdir()
        if entry.is_dir() and entry.joinpath("SKILL.md").is_file()
    )


def _materialize_template_dir(template_dir: Path) -> Path:
    bundled_root = zdx_template_dir()
    if template_dir == bundled_root:
        return bundled_root
    template_dir.mkdir(parents=True, exist_ok=True)
    for filename in ("manifest.json", "SOUL.md"):
        target = template_dir / filename
        if not target.exists():
            target.write_bytes((bundled_root / filename).read_bytes())
    return template_dir


def read_zdx_template(template_dir: Path | None = None) -> dict[str, Any]:
    bundled_root = zdx_template_dir()
    root = _materialize_template_dir(template_dir or bundled_root)
    manifest = json.loads((root / "manifest.json").read_text(encoding="utf-8"))
    general_manifest_path = bundled_root.parent / "general-assistant" / "manifest.json"
    general_manifest: dict[str, Any] = {}
    if general_manifest_path.is_file():
        try:
            loaded = json.loads(general_manifest_path.read_text(encoding="utf-8"))
            if isinstance(loaded, dict):
                general_manifest = loaded
        except (OSError, json.JSONDecodeError):
            general_manifest = {}
    return {
        "id": ZDX_EXPERT_ID,
        "version": str(manifest.get("template_version") or ZDX_TEMPLATE_VERSION),
        "label": manifest.get("label") or {"zh": "通联发仔", "en": "Tonglian Fazai"},
        "description": manifest.get("description") or {"zh": "", "en": ""},
        "welcome_message": manifest.get("welcome_message") or {"zh": "", "en": ""},
        "icon_url": manifest.get("icon_url") or ZDX_ICON_URL,
        "soul": (root / "SOUL.md").read_text(encoding="utf-8"),
        "quick_prompts": manifest.get("quick_prompts")
        or general_manifest.get("quick_prompts")
        or [],
        "builtin_skill_slugs": manifest.get("builtin_skill_slugs") or list_builtin_skill_slugs(),
        "skill_package_ids": manifest.get("skill_package_ids") or [],
        "task_examples": manifest.get("task_examples")
        or general_manifest.get("task_examples")
        or {"zh": [], "en": []},
        "managed_model": manifest.get("managed_model")
        or {
            "type": "tonglian_zdx",
            "base_url": ZDX_PROVIDER_BASE_URL,
            "model": ZDX_MODEL_ID,
            "credential_scope": "current_user",
            "mode": "direct",
        },
    }


def write_zdx_template(
    template: dict[str, Any], *, template_dir: Path | None = None
) -> dict[str, Any]:
    root = _materialize_template_dir(template_dir or zdx_template_dir())
    manifest = json.loads((root / "manifest.json").read_text(encoding="utf-8"))
    for key in (
        "label",
        "description",
        "welcome_message",
        "icon_url",
        "quick_prompts",
        "builtin_skill_slugs",
        "skill_package_ids",
        "task_examples",
        "managed_model",
    ):
        if key in template:
            manifest[key] = template[key]
    manifest["template_version"] = str(template["version"])
    (root / "manifest.json").write_text(
        json.dumps(manifest, ensure_ascii=False, indent=2) + "\n", encoding="utf-8"
    )
    (root / "SOUL.md").write_text(str(template["soul"]), encoding="utf-8")
    return read_zdx_template(template_dir=root)


def remove_legacy_zdx_provider(provider_repo: Any, agent_repo: Any) -> None:
    """Remove the old phase-one Provider row when it is no longer referenced."""
    existing = provider_repo.get_by_name(ZDX_PROVIDER_NAME)
    if existing is None:
        return
    for row in agent_repo.list_all():
        config = json.loads(row.config_json or "{}")
        if ZDX_PROVIDER_NAME in (config.get("providers") or []):
            return
        if str(row.default_model or "").startswith(f"{ZDX_PROVIDER_NAME}/"):
            return
    provider_repo.delete(existing.id)


async def ensure_zdx_agent(
    registry: Any,
    catalog: Any,
    *,
    user_id: int,
    locale: str,
    template_dir: Path | None = None,
) -> Any:
    """Create the user's single managed Tonglian Fazai agent when missing."""
    existing = [
        row
        for row in registry.list_agents(user_id)
        if getattr(row, "managed_type", None) == MANAGED_ZDX_TYPE
    ]
    if existing:
        row = existing[0]
        icon_url = str(read_zdx_template(template_dir).get("icon_url") or "").strip()
        if icon_url and getattr(row, "icon_url", None) != icon_url:
            return registry.set_icon_url(row.agent_id, icon_url)
        return row
    expert = catalog.get(ZDX_EXPERT_ID)
    if expert is None:
        raise RuntimeError(f"managed expert template missing: {ZDX_EXPERT_ID}")
    template = read_zdx_template(template_dir)
    spec = build_create_spec_from_expert(
        expert_id=ZDX_EXPERT_ID,
        expert=expert,
        user_id=user_id,
        name="通联发仔" if locale == "zh" else "Tonglian Fazai",
        locale=locale,
        config_extra={
            "backend": default_home_local_backend(),
            "managed_model": template["managed_model"],
        },
    )
    spec.description = str(template.get("description", {}).get(locale) or spec.description)
    spec.system_prompt = str(template["soul"])
    spec.welcome_message = str(template.get("welcome_message", {}).get(locale) or "")
    spec.icon_url = str(template.get("icon_url") or spec.icon_url or "") or None
    spec.managed_type = MANAGED_ZDX_TYPE
    spec.config_locked = True
    spec.template_version = str(template["version"])
    return await registry.create(spec, defer_bootstrap=True)


__all__ = [
    "ZDX_PROVIDER_NAME",
    "ZDX_PROVIDER_LABEL",
    "ZDX_PROVIDER_BASE_URL",
    "ZDX_MODEL_ID",
    "MANAGED_ZDX_TYPE",
    "ZDX_EXPERT_ID",
    "ZDX_TEMPLATE_VERSION",
    "ZDX_ICON_URL",
    "zdx_template_dir",
    "list_builtin_skill_slugs",
    "read_zdx_template",
    "write_zdx_template",
    "remove_legacy_zdx_provider",
    "ensure_zdx_agent",
]
