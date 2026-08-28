"""Tests for the Presence Lighting controller runtime."""

from homeassistant.const import (
    ATTR_ENTITY_ID,
    CONF_NAME,
    SERVICE_TURN_OFF,
    SERVICE_TURN_ON,
    STATE_OFF,
    STATE_ON,
    STATE_UNAVAILABLE,
    Platform,
)
from homeassistant.core import HomeAssistant, ServiceCall
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
    TYPE_PRESENCE_LIGHTING,
)
from custom_components.adaptive_control.models import EntryKind
from custom_components.adaptive_control.presence_lighting import (
    PresenceLightingProfile,
    PresenceLightingRuntime,
)

OCCUPANCY = "binary_sensor.bathroom_occupancy"
ILLUMINANCE = "sensor.bathroom_illuminance"
NIGHT = "sun.sun"
MAIN_LIGHT = "switch.bathroom_main"
DAY_SCENE = "scene.bathroom_day"
NIGHT_SCENE = "scene.bathroom_night"
VACANT_SCENE = "scene.bathroom_off"


def make_runtime(hass: HomeAssistant) -> PresenceLightingRuntime:
    """Create one Presence Lighting runtime."""
    entry = MockConfigEntry(
        domain="adaptive_control",
        title="Bathroom Lighting",
        data={
            CONF_NAME: "Bathroom Lighting",
            CONF_ENTRY_KIND: EntryKind.CONTROLLER,
            CONF_TYPE_ID: TYPE_PRESENCE_LIGHTING,
            CONF_OCCUPANCY_ENTITY_ID: OCCUPANCY,
            CONF_ILLUMINANCE_ENTITY_ID: ILLUMINANCE,
            CONF_NIGHT_ENTITY_ID: NIGHT,
            CONF_MAIN_LIGHT_ENTITY_ID: MAIN_LIGHT,
            CONF_DAY_SCENE_ENTITY_ID: DAY_SCENE,
            CONF_NIGHT_SCENE_ENTITY_ID: NIGHT_SCENE,
            CONF_VACANT_SCENE_ENTITY_ID: VACANT_SCENE,
            CONF_ILLUMINANCE_THRESHOLD: 100,
        },
        version=1,
    )
    return PresenceLightingRuntime(hass, entry)


def register_services(hass: HomeAssistant) -> list[tuple[str, str, str]]:
    """Register actuator services and return recorded calls."""
    calls: list[tuple[str, str, str]] = []

    async def record(call: ServiceCall) -> None:
        calls.append((call.domain, call.service, call.data[ATTR_ENTITY_ID]))
        if call.domain == Platform.SWITCH:
            hass.states.async_set(
                call.data[ATTR_ENTITY_ID],
                STATE_ON if call.service == SERVICE_TURN_ON else STATE_OFF,
            )

    hass.services.async_register(Platform.SWITCH, SERVICE_TURN_ON, record)
    hass.services.async_register(Platform.SWITCH, SERVICE_TURN_OFF, record)
    hass.services.async_register(Platform.SCENE, SERVICE_TURN_ON, record)
    return calls


async def test_snapshots_entry_lux_without_repeating_transition_actions(
    hass: HomeAssistant,
) -> None:
    """Light output cannot feed back into the occupied daytime profile."""
    calls = register_services(hass)
    hass.states.async_set(OCCUPANCY, STATE_ON)
    hass.states.async_set(ILLUMINANCE, "50")
    hass.states.async_set(NIGHT, "above_horizon")
    hass.states.async_set(MAIN_LIGHT, STATE_OFF)
    hass.states.async_set(DAY_SCENE, "unknown")
    hass.states.async_set(NIGHT_SCENE, "unknown")
    hass.states.async_set(VACANT_SCENE, "unknown")
    runtime = make_runtime(hass)
    await runtime.async_start()

    assert runtime.effective_profile is PresenceLightingProfile.DISABLED
    assert not calls

    await runtime.async_set_enabled(True)
    assert runtime.effective_profile is PresenceLightingProfile.OCCUPIED_DARK
    assert calls == [
        (Platform.SWITCH, SERVICE_TURN_ON, MAIN_LIGHT),
        (Platform.SCENE, SERVICE_TURN_ON, DAY_SCENE),
    ]

    await runtime.async_evaluate("same_inputs")
    assert len(calls) == 2

    hass.states.async_set(ILLUMINANCE, "250")
    await hass.async_block_till_done()
    assert runtime.effective_profile is PresenceLightingProfile.OCCUPIED_DARK
    assert len(calls) == 2
    assert calls.count((Platform.SCENE, SERVICE_TURN_ON, DAY_SCENE)) == 1

    hass.states.async_set(OCCUPANCY, STATE_OFF)
    await hass.async_block_till_done()
    assert runtime.effective_profile is PresenceLightingProfile.VACANT
    assert calls[-1] == (Platform.SCENE, SERVICE_TURN_ON, VACANT_SCENE)

    hass.states.async_set(OCCUPANCY, STATE_ON)
    await hass.async_block_till_done()
    assert runtime.effective_profile is PresenceLightingProfile.OCCUPIED_BRIGHT
    assert calls[-1] == (Platform.SCENE, SERVICE_TURN_ON, DAY_SCENE)
    assert calls.count((Platform.SWITCH, SERVICE_TURN_OFF, MAIN_LIGHT)) == 1
    await runtime.async_stop()


async def test_night_profile_does_not_require_illuminance(
    hass: HomeAssistant,
) -> None:
    """Night presence uses its transition scene and keeps the main light off."""
    calls = register_services(hass)
    hass.states.async_set(OCCUPANCY, STATE_ON)
    hass.states.async_set(ILLUMINANCE, STATE_UNAVAILABLE)
    hass.states.async_set(NIGHT, "below_horizon")
    hass.states.async_set(MAIN_LIGHT, STATE_ON)
    hass.states.async_set(NIGHT_SCENE, "unknown")
    runtime = make_runtime(hass)
    await runtime.async_start()

    await runtime.async_set_enabled(True)

    assert runtime.effective_profile is PresenceLightingProfile.OCCUPIED_NIGHT
    assert calls == [
        (Platform.SWITCH, SERVICE_TURN_OFF, MAIN_LIGHT),
        (Platform.SCENE, SERVICE_TURN_ON, NIGHT_SCENE),
    ]
    await runtime.async_stop()


async def test_unavailable_presence_preserves_outputs_but_vacancy_turns_them_off(
    hass: HomeAssistant,
) -> None:
    """An uncertain occupied state never causes a speculative command."""
    calls = register_services(hass)
    hass.states.async_set(OCCUPANCY, STATE_UNAVAILABLE)
    hass.states.async_set(ILLUMINANCE, "20")
    hass.states.async_set(NIGHT, "above_horizon")
    hass.states.async_set(MAIN_LIGHT, STATE_ON)
    hass.states.async_set(VACANT_SCENE, "unknown")
    runtime = make_runtime(hass)
    await runtime.async_start()

    await runtime.async_set_enabled(True)
    assert runtime.effective_profile is PresenceLightingProfile.INPUT_UNAVAILABLE
    assert not calls

    hass.states.async_set(OCCUPANCY, STATE_OFF)
    await hass.async_block_till_done()
    assert runtime.effective_profile is PresenceLightingProfile.VACANT
    assert calls == [
        (Platform.SWITCH, SERVICE_TURN_OFF, MAIN_LIGHT),
        (Platform.SCENE, SERVICE_TURN_ON, VACANT_SCENE),
    ]
    await runtime.async_stop()


async def test_disabled_controller_ignores_signal_changes(
    hass: HomeAssistant,
) -> None:
    """Disabling automatic control preserves current actuator state."""
    calls = register_services(hass)
    hass.states.async_set(OCCUPANCY, STATE_OFF)
    hass.states.async_set(ILLUMINANCE, "20")
    hass.states.async_set(NIGHT, "above_horizon")
    hass.states.async_set(MAIN_LIGHT, STATE_OFF)
    hass.states.async_set(VACANT_SCENE, "unknown")
    runtime = make_runtime(hass)
    await runtime.async_start()
    await runtime.async_set_enabled(True)
    calls.clear()

    await runtime.async_set_enabled(False)
    hass.states.async_set(OCCUPANCY, STATE_ON)
    await hass.async_block_till_done()

    assert runtime.effective_profile is PresenceLightingProfile.DISABLED
    assert not calls
    await runtime.async_stop()
