"""Runtime capabilities for system-managed agents.

Managed agents may use a model/runtime that is not the normal Harness
provider pipeline.  Keep that distinction in one registry so channels,
chat preparation, and management APIs do not each key off an agent name.
"""

from __future__ import annotations

from dataclasses import dataclass
from typing import Any, Literal

MANAGED_ZDX_TYPE = "tonglian_fazai"

ManagedExecutionMode = Literal["harness", "direct_model"]
ChannelDeliveryMode = Literal["invoke", "stream"]


@dataclass(frozen=True)
class ManagedAgentCapabilities:
    execution_mode: ManagedExecutionMode = "harness"
    supports_channels: bool = True
    supports_connectors: bool = True
    supports_harness_tools: bool = True
    supports_skills: bool = True
    supports_knowledge_bases: bool = True
    supports_workspace: bool = True
    supports_model_override: bool = True
    supports_subagents: bool = True
    qq_delivery_mode: ChannelDeliveryMode = "stream"

    @property
    def direct_model(self) -> bool:
        return self.execution_mode == "direct_model"

    def as_dict(self) -> dict[str, Any]:
        return {
            "execution_mode": self.execution_mode,
            "direct_model": self.direct_model,
            "supports_channels": self.supports_channels,
            "supports_connectors": self.supports_connectors,
            "supports_harness_tools": self.supports_harness_tools,
            "supports_skills": self.supports_skills,
            "supports_knowledge_bases": self.supports_knowledge_bases,
            "supports_workspace": self.supports_workspace,
            "supports_model_override": self.supports_model_override,
            "supports_subagents": self.supports_subagents,
            "qq_delivery_mode": self.qq_delivery_mode,
        }


STANDARD_AGENT_CAPABILITIES = ManagedAgentCapabilities()

MANAGED_AGENT_CAPABILITIES: dict[str, ManagedAgentCapabilities] = {
    MANAGED_ZDX_TYPE: ManagedAgentCapabilities(
        execution_mode="direct_model",
        supports_connectors=False,
        supports_harness_tools=False,
        supports_skills=False,
        supports_knowledge_bases=False,
        supports_workspace=False,
        supports_model_override=False,
        supports_subagents=False,
        qq_delivery_mode="invoke",
    )
}


def capabilities_for_type(managed_type: str | None) -> ManagedAgentCapabilities:
    if not managed_type:
        return STANDARD_AGENT_CAPABILITIES
    return MANAGED_AGENT_CAPABILITIES.get(managed_type, STANDARD_AGENT_CAPABILITIES)


def capabilities_for_row(row: Any | None) -> ManagedAgentCapabilities:
    return capabilities_for_type(getattr(row, "managed_type", None) if row else None)


def is_managed_agent(row: Any | None) -> bool:
    return bool(getattr(row, "managed_type", None)) if row is not None else False


def is_direct_model_agent(row: Any | None) -> bool:
    return capabilities_for_row(row).direct_model


__all__ = [
    "ChannelDeliveryMode",
    "ManagedAgentCapabilities",
    "ManagedExecutionMode",
    "MANAGED_AGENT_CAPABILITIES",
    "MANAGED_ZDX_TYPE",
    "STANDARD_AGENT_CAPABILITIES",
    "capabilities_for_row",
    "capabilities_for_type",
    "is_direct_model_agent",
    "is_managed_agent",
]
