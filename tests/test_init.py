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
    CONF_DAY_SCENE_ENTITY_ID,
    CONF_ENTRY_KIND,
    CONF_ILLUMINANCE_ENTITY_ID,
    CONF_ILLUMINANCE_THRESHOLD,
    CONF_MAIN_LIGHT_ENTITY_ID,
    CONF_NIGHT_ENTITY_ID,
    CONF_NIGHT_SCENE_ENTITY_ID,
    CONF_OCCUPANCY_ENTITY_ID,
    CONF_TYPE_ID,
    CONF_VACANT_SCENE_ENTITY_ID,
    DOMAIN,
    TYPE_PRESENCE_LIGHTING,
)
from custom_components.adaptive_control.diagnostics import (
    async_get_config_entry_diagnostics,
)
from custom_components.adaptive_control.models import EntryKind


async def test_setup_exposes_and_restores_common_observability(
    hass: HomeAssistant,
) -> None:
    """A runtime entry owns a restorable logging switch and bounded diagnostics."""
    hass.states.async_set("binary_sensor.bathroom_occupancy", STATE_OFF)
    hass.states.async_set("sensor.bathroom_illuminance", "50")
    hass.states.async_set("sun.sun", "above_horizon")
    hass.states.async_set("switch.bathroom_main", STATE_OFF)
    hass.states.async_set("scene.bathroom_day", "unknown")
    hass.states.async_set("scene.bathroom_night", "unknown")
    hass.states.async_set("scene.bathroom_off", "unknown")
    scene_calls = []

    async def record_scene(call) -> None:
        scene_calls.append(call.data[ATTR_ENTITY_ID])

    hass.services.async_register(Platform.SCENE, SERVICE_TURN_ON, record_scene)
    entry = MockConfigEntry(
        domain=DOMAIN,
        title="Bathroom Lighting",
        data={
            CONF_NAME: "Bathroom Lighting",
            CONF_ENTRY_KIND: EntryKind.CONTROLLER,
            CONF_TYPE_ID: TYPE_PRESENCE_LIGHTING,
            CONF_OCCUPANCY_ENTITY_ID: "binary_sensor.bathroom_occupancy",
            CONF_ILLUMINANCE_ENTITY_ID: "sensor.bathroom_illuminance",
            CONF_NIGHT_ENTITY_ID: "sun.sun",
            CONF_MAIN_LIGHT_ENTITY_ID: "switch.bathroom_main",
            CONF_DAY_SCENE_ENTITY_ID: "scene.bathroom_day",
            CONF_NIGHT_SCENE_ENTITY_ID: "scene.bathroom_night",
            CONF_VACANT_SCENE_ENTITY_ID: "scene.bathroom_off",
            CONF_ILLUMINANCE_THRESHOLD: 100,
        },
        version=1,
    )
    entry.add_to_hass(hass)

    assert await hass.config_entries.async_setup(entry.entry_id)
    await hass.async_block_till_done()

    registry = er.async_get(hass)
    enabled_entry = next(
        item
        for item in er.async_entries_for_config_entry(registry, entry.entry_id)
        if item.unique_id == f"{entry.entry_id}_enabled"
    )
    verbose_entry = next(
        item
        for item in er.async_entries_for_config_entry(registry, entry.entry_id)
        if item.unique_id == f"{entry.entry_id}_verbose_logging"
    )
    profile_entry = next(
        item
        for item in er.async_entries_for_config_entry(registry, entry.entry_id)
        if item.unique_id == f"{entry.entry_id}_effective_profile"
    )
    decision_entry = next(
        item
        for item in er.async_entries_for_config_entry(registry, entry.entry_id)
        if item.unique_id == f"{entry.entry_id}_decision"
    )
    assert verbose_entry.device_id is not None
    assert enabled_entry.device_id == verbose_entry.device_id
    assert profile_entry.device_id == verbose_entry.device_id
    assert decision_entry.device_id == verbose_entry.device_id
    assert verbose_entry.entity_category is EntityCategory.CONFIG
    assert hass.states.get(enabled_entry.entity_id).state == STATE_OFF
    assert hass.states.get(verbose_entry.entity_id).state == STATE_OFF
    assert hass.states.get(profile_entry.entity_id).state == "disabled"
    assert not scene_calls

    await hass.services.async_call(
        Platform.SWITCH,
        SERVICE_TURN_ON,
        {ATTR_ENTITY_ID: verbose_entry.entity_id},
        blocking=True,
    )
    assert entry.runtime_data.verbose_logging_enabled
    assert hass.states.get(verbose_entry.entity_id).state == STATE_ON

    await hass.services.async_call(
        Platform.SWITCH,
        SERVICE_TURN_ON,
        {ATTR_ENTITY_ID: enabled_entry.entity_id},
        blocking=True,
    )
    await hass.async_block_till_done()
    assert entry.runtime_data.enabled
    assert hass.states.get(enabled_entry.entity_id).state == STATE_ON
    assert hass.states.get(profile_entry.entity_id).state == "vacant"
    assert scene_calls == ["scene.bathroom_off"]

    decision = entry.runtime_data.record_decision(
        "profile_selected",
        "presence_detected",
        {"profile": "occupied"},
    )
    diagnostics = await async_get_config_entry_diagnostics(hass, entry)
    assert diagnostics["runtime"]["decision_trace"][-1] == decision.as_dict()
    await hass.async_block_till_done()
    decision_state = hass.states.get(decision_entry.entity_id)
    assert decision_state.attributes["event_type"] == "profile_selected"
    assert decision_state.attributes["decision_id"] == decision.decision_id

    assert await hass.config_entries.async_unload(entry.entry_id)
    assert await hass.config_entries.async_setup(entry.entry_id)
    await hass.async_block_till_done()
    assert entry.runtime_data.verbose_logging_enabled
    assert entry.runtime_data.enabled
    assert all(
        restored.decision_id != decision.decision_id
        for restored in entry.runtime_data.decision_trace
    )
    assert hass.states.get(enabled_entry.entity_id).state == STATE_ON
    assert hass.states.get(verbose_entry.entity_id).state == STATE_ON
    assert hass.states.get(profile_entry.entity_id).state == "vacant"
    assert await hass.config_entries.async_unload(entry.entry_id)
