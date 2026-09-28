from types import SimpleNamespace

from octop.infra.agents.managed_runtime import (
    MANAGED_ZDX_TYPE,
    capabilities_for_row,
    capabilities_for_type,
    is_direct_model_agent,
)


def test_standard_agent_keeps_harness_capabilities() -> None:
    capabilities = capabilities_for_row(SimpleNamespace(managed_type=None))

    assert capabilities.execution_mode == "harness"
    assert capabilities.supports_connectors
    assert capabilities.supports_harness_tools
    assert capabilities.supports_skills
    assert capabilities.supports_knowledge_bases
    assert capabilities.supports_workspace
    assert capabilities.supports_model_override


def test_tonglian_agent_uses_direct_model_capabilities() -> None:
    capabilities = capabilities_for_type(MANAGED_ZDX_TYPE)

    assert is_direct_model_agent(SimpleNamespace(managed_type=MANAGED_ZDX_TYPE))
    assert capabilities.execution_mode == "direct_model"
    assert not capabilities.supports_connectors
    assert not capabilities.supports_harness_tools
    assert not capabilities.supports_skills
    assert not capabilities.supports_knowledge_bases
    assert not capabilities.supports_workspace
    assert not capabilities.supports_model_override
    assert capabilities.qq_delivery_mode == "invoke"


def test_unknown_managed_type_falls_back_to_standard_runtime() -> None:
    capabilities = capabilities_for_type("future_managed_agent")

    assert capabilities.execution_mode == "harness"
    assert capabilities.as_dict()["direct_model"] is False
