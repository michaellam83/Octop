"""Tests for system-managed ZDX provisioning metadata."""

from __future__ import annotations

from pathlib import Path

from octop.infra.agents.managed_agent import (
    ZDX_ICON_URL,
    ZDX_PROVIDER_NAME,
    read_zdx_template,
    remove_legacy_zdx_provider,
    write_zdx_template,
)
from octop.infra.db.migrate import run_migrations
from octop.infra.db.pool import SqlitePool
from octop.infra.db.repos.agents import AgentRepo
from octop.infra.db.repos.providers import ProviderRepo


def test_remove_legacy_zdx_provider_removes_unreferenced_row(tmp_path: Path) -> None:
    db = SqlitePool(tmp_path / "octop.db")
    run_migrations(db)
    providers = ProviderRepo(db)
    agents = AgentRepo(db)
    providers.create(name=ZDX_PROVIDER_NAME, kind="openai")

    remove_legacy_zdx_provider(providers, agents)

    assert providers.get_by_name(ZDX_PROVIDER_NAME) is None


def test_zdx_template_uses_bundled_portrait() -> None:
    template = read_zdx_template()

    assert template["icon_url"] == ZDX_ICON_URL


def test_zdx_template_writes_to_instance_storage(tmp_path: Path) -> None:
    template_dir = tmp_path / "managed-templates" / "tonglian-fazai"
    template = read_zdx_template(template_dir)

    updated = write_zdx_template(
        {**template, "version": "99", "soul": "instance template"},
        template_dir=template_dir,
    )

    assert updated["version"] == "99"
    assert updated["soul"] == "instance template"
    assert read_zdx_template()["version"] != "99"
