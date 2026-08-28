"""Tests for the shared Adaptive Control runtime."""

import logging

import pytest
from homeassistant.const import CONF_NAME
from homeassistant.core import HomeAssistant
from pytest_homeassistant_custom_component.common import MockConfigEntry

from custom_components.adaptive_control import runtime as runtime_module
from custom_components.adaptive_control.const import (
    CONF_ENTRY_KIND,
    CONF_TYPE_ID,
    DOMAIN,
    MAX_DECISION_TRACE,
)
from custom_components.adaptive_control.models import EntryKind
from custom_components.adaptive_control.runtime import AdaptiveRuntime


def make_runtime(hass: HomeAssistant, title: str) -> AdaptiveRuntime:
    """Create one runtime without starting an integration entry."""
    entry = MockConfigEntry(
        domain=DOMAIN,
        title=title,
        data={
            CONF_NAME: title,
            CONF_ENTRY_KIND: EntryKind.CONTROLLER,
            CONF_TYPE_ID: "test_controller",
        },
        version=1,
    )
    return AdaptiveRuntime(hass, entry)


def test_decision_trace_is_bounded(hass: HomeAssistant) -> None:
    """Only the newest diagnostic decisions are retained."""
    runtime = make_runtime(hass, "Bounded")

    for index in range(MAX_DECISION_TRACE + 3):
        runtime.record_decision(
            f"event_{index}",
            "test",
            {"index": index},
        )

    assert len(runtime.decision_trace) == MAX_DECISION_TRACE
    assert runtime.decision_trace[0].event == "event_3"
    assert runtime.decision_trace[-1].details == {"index": MAX_DECISION_TRACE + 2}


def test_verbose_logging_is_scoped_to_one_runtime(
    hass: HomeAssistant,
    caplog: pytest.LogCaptureFixture,
) -> None:
    """Only the enabled entry promotes detailed messages to the normal log."""
    enabled = make_runtime(hass, "Enabled")
    disabled = make_runtime(hass, "Disabled")
    caplog.set_level(logging.INFO, logger=runtime_module.__name__)

    enabled.async_set_verbose_logging(True)
    caplog.clear()
    enabled._log_verbose("enabled runtime detail")
    disabled._log_verbose("disabled runtime detail")

    assert "enabled runtime detail" in caplog.text
    assert "disabled runtime detail" not in caplog.text
    assert enabled.diagnostics()["verbose_logging_enabled"]
    assert not disabled.diagnostics()["verbose_logging_enabled"]
