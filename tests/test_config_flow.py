"""Tests for the Adaptive Control config flow."""

from homeassistant.const import CONF_NAME
from homeassistant.core import HomeAssistant
from homeassistant.data_entry_flow import FlowResultType
from pytest_homeassistant_custom_component.common import MockConfigEntry

from custom_components.adaptive_control.config_flow import AdaptiveControlConfigFlow
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
    TYPE_PRESENCE_LIGHTING,
)
from custom_components.adaptive_control.models import EntryKind


def presence_lighting_input(**updates) -> dict:
    """Return one valid Presence Lighting form submission."""
    data = {
        CONF_NAME: "Bathroom Lighting",
        CONF_OCCUPANCY_ENTITY_ID: "binary_sensor.bathroom_occupancy",
        CONF_ILLUMINANCE_ENTITY_ID: "sensor.bathroom_illuminance",
        CONF_NIGHT_ENTITY_ID: "sun.sun",
        CONF_MAIN_LIGHT_ENTITY_ID: "switch.bathroom_main",
        CONF_DAY_SCENE_ENTITY_ID: "scene.bathroom_day",
        CONF_NIGHT_SCENE_ENTITY_ID: "scene.bathroom_night",
        CONF_VACANT_SCENE_ENTITY_ID: "scene.bathroom_off",
        CONF_ILLUMINANCE_THRESHOLD: 100,
    }
    return data | updates


async def test_user_flow_creates_typed_presence_lighting_entry(
    hass: HomeAssistant,
) -> None:
    """Every UI-created entry has explicit type, input, and actuator bindings."""
    flow = AdaptiveControlConfigFlow()
    flow.hass = hass

    result = await flow.async_step_user()

    assert result["type"] is FlowResultType.FORM
    assert result["step_id"] == "user"

    result = await flow.async_step_user(presence_lighting_input())

    assert result["type"] is FlowResultType.CREATE_ENTRY
    assert result["title"] == "Bathroom Lighting"
    assert result["data"][CONF_ENTRY_KIND] is EntryKind.CONTROLLER
    assert result["data"][CONF_TYPE_ID] == TYPE_PRESENCE_LIGHTING


async def test_user_flow_rejects_an_actuator_owned_by_another_controller(
    hass: HomeAssistant,
) -> None:
    """One actuator cannot be automatically commanded by two controllers."""
    existing = MockConfigEntry(
        domain="adaptive_control",
        title="Existing",
        data=presence_lighting_input()
        | {
            CONF_ENTRY_KIND: EntryKind.CONTROLLER,
            CONF_TYPE_ID: TYPE_PRESENCE_LIGHTING,
        },
    )
    existing.add_to_hass(hass)
    flow = AdaptiveControlConfigFlow()
    flow.hass = hass

    result = await flow.async_step_user(presence_lighting_input())

    assert result["type"] is FlowResultType.FORM
    assert result["errors"] == {CONF_MAIN_LIGHT_ENTITY_ID: "actuator_already_owned"}


async def test_reconfigure_updates_bindings_and_policy(
    hass: HomeAssistant,
) -> None:
    """Reconfigure preserves the type and reloads the updated entry."""
    entry = MockConfigEntry(
        domain="adaptive_control",
        title="Bathroom Lighting",
        data=presence_lighting_input()
        | {
            CONF_ENTRY_KIND: EntryKind.CONTROLLER,
            CONF_TYPE_ID: TYPE_PRESENCE_LIGHTING,
        },
    )
    entry.add_to_hass(hass)
    flow = AdaptiveControlConfigFlow()
    flow.hass = hass
    flow.context = {"source": "reconfigure", "entry_id": entry.entry_id}

    result = await flow.async_step_reconfigure(
        presence_lighting_input(
            **{
                CONF_NAME: "Updated Bathroom Lighting",
                CONF_ILLUMINANCE_THRESHOLD: 175,
            }
        )
    )

    assert result["type"] is FlowResultType.ABORT
    assert result["reason"] == "reconfigure_successful"
    assert entry.title == "Updated Bathroom Lighting"
    assert entry.data[CONF_ILLUMINANCE_THRESHOLD] == 175
