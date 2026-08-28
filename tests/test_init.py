"""Integration setup tests for Adaptive Control."""

from homeassistant.const import (
    ATTR_ENTITY_ID,
    CONF_NAME,
    SERVICE_TURN_ON,
    STATE_OFF,
    STATE_ON,
    EntityCategory,
    Platform,
)
from homeassistant.core import HomeAssistant
from homeassistant.helpers import entity_registry as er
from pytest_homeassistant_custom_component.common import MockConfigEntry

from custom_components.adaptive_control.const import (
    CONF_ENTRY_KIND,
    CONF_TYPE_ID,
    DOMAIN,
)
from custom_components.adaptive_control.diagnostics import (
    async_get_config_entry_diagnostics,
)
from custom_components.adaptive_control.models import EntryKind


async def test_setup_exposes_and_restores_common_observability(
    hass: HomeAssistant,
) -> None:
    """A runtime entry owns a restorable logging switch and bounded diagnostics."""
    entry = MockConfigEntry(
        domain=DOMAIN,
        title="Bathroom Lighting",
        data={
            CONF_NAME: "Bathroom Lighting",
            CONF_ENTRY_KIND: EntryKind.CONTROLLER,
            CONF_TYPE_ID: "adaptive_lighting",
        },
        version=1,
    )
    entry.add_to_hass(hass)

    assert await hass.config_entries.async_setup(entry.entry_id)
    await hass.async_block_till_done()

    registry = er.async_get(hass)
    verbose_entry = next(
        item
        for item in er.async_entries_for_config_entry(registry, entry.entry_id)
        if item.unique_id == f"{entry.entry_id}_verbose_logging"
    )
    assert verbose_entry.device_id is not None
    assert verbose_entry.entity_category is EntityCategory.CONFIG
    assert hass.states.get(verbose_entry.entity_id).state == STATE_OFF

    await hass.services.async_call(
        Platform.SWITCH,
        SERVICE_TURN_ON,
        {ATTR_ENTITY_ID: verbose_entry.entity_id},
        blocking=True,
    )
    assert entry.runtime_data.verbose_logging_enabled
    assert hass.states.get(verbose_entry.entity_id).state == STATE_ON

    decision = entry.runtime_data.record_decision(
        "profile_selected",
        "presence_detected",
        {"profile": "occupied"},
    )
    diagnostics = await async_get_config_entry_diagnostics(hass, entry)
    assert diagnostics["runtime"]["decision_trace"] == [decision.as_dict()]

    assert await hass.config_entries.async_unload(entry.entry_id)
    assert await hass.config_entries.async_setup(entry.entry_id)
    await hass.async_block_till_done()
    assert entry.runtime_data.verbose_logging_enabled
    assert entry.runtime_data.decision_trace == ()
    assert hass.states.get(verbose_entry.entity_id).state == STATE_ON
    assert await hass.config_entries.async_unload(entry.entry_id)
