"""Tests for the initial Adaptive Control config flow contract."""

from homeassistant.data_entry_flow import FlowResultType

from custom_components.adaptive_control.config_flow import AdaptiveControlConfigFlow


async def test_user_flow_cannot_create_an_untyped_entry() -> None:
    """The foundation does not expose a meaningless generic controller."""
    result = await AdaptiveControlConfigFlow().async_step_user()

    assert result["type"] is FlowResultType.ABORT
    assert result["reason"] == "no_controller_types"
