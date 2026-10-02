"""Presence Lighting Controller Type."""

from __future__ import annotations

import asyncio
import logging
import math
from collections.abc import Callable
from enum import StrEnum
from typing import Any

from homeassistant.config_entries import ConfigEntry
from homeassistant.const import (
    ATTR_ENTITY_ID,
    SERVICE_TURN_OFF,
    SERVICE_TURN_ON,
    STATE_OFF,
    STATE_ON,
    STATE_UNAVAILABLE,
    STATE_UNKNOWN,
)
from homeassistant.core import Event, EventStateChangedData, HomeAssistant, callback
from homeassistant.exceptions import HomeAssistantError
from homeassistant.helpers.event import async_track_state_change_event

from .const import (
    CONF_DAY_SCENE_ENTITY_ID,
    CONF_ILLUMINANCE_ENTITY_ID,
    CONF_ILLUMINANCE_THRESHOLD,
    CONF_MAIN_LIGHT_ENTITY_ID,
    CONF_NIGHT_ENTITY_ID,
    CONF_NIGHT_SCENE_ENTITY_ID,
    CONF_OCCUPANCY_ENTITY_ID,
    CONF_VACANT_SCENE_ENTITY_ID,
)
from .models import SignalQuality
from .runtime import AdaptiveRuntime

_LOGGER = logging.getLogger(__name__)


class PresenceLightingProfile(StrEnum):
    """Effective profiles supported by Presence Lighting."""

    DISABLED = "disabled"
    INPUT_UNAVAILABLE = "input_unavailable"
    VACANT = "vacant"
    OCCUPIED_BRIGHT = "occupied_bright"
    OCCUPIED_DARK = "occupied_dark"
    OCCUPIED_NIGHT = "occupied_night"


class PresenceLightingRuntime(AdaptiveRuntime):
    """Select and apply a lighting profile from occupancy, night, and lux."""

    def __init__(self, hass: HomeAssistant, entry: ConfigEntry) -> None:
        """Initialize one Presence Lighting controller."""
        super().__init__(hass, entry)
        data = entry.data
        self.occupancy_entity_id = data[CONF_OCCUPANCY_ENTITY_ID]
        self.illuminance_entity_id = data[CONF_ILLUMINANCE_ENTITY_ID]
        self.night_entity_id = data[CONF_NIGHT_ENTITY_ID]
        self.main_light_entity_id = data[CONF_MAIN_LIGHT_ENTITY_ID]
        self.day_scene_entity_id = data[CONF_DAY_SCENE_ENTITY_ID]
        self.night_scene_entity_id = data[CONF_NIGHT_SCENE_ENTITY_ID]
        self.vacant_scene_entity_id = data[CONF_VACANT_SCENE_ENTITY_ID]
        self.illuminance_threshold = float(data[CONF_ILLUMINANCE_THRESHOLD])
        self._effective_profile = PresenceLightingProfile.DISABLED
        self._signal_quality = {
            "occupancy": SignalQuality.UNAVAILABLE,
            "illuminance": SignalQuality.UNAVAILABLE,
            "night": SignalQuality.UNAVAILABLE,
        }
        self._entry_illuminance: float | None = None
        self._occupied_day_profile: PresenceLightingProfile | None = None
        self._evaluate_lock = asyncio.Lock()
        self._remove_state_listener: Callable[[], None] | None = None

    async def async_start(self) -> None:
        """Subscribe to input changes without commanding outputs while disabled."""
        await super().async_start()
        self._remove_state_listener = async_track_state_change_event(
            self.hass,
            (
                self.occupancy_entity_id,
                self.illuminance_entity_id,
                self.night_entity_id,
            ),
            self._async_input_changed,
        )
        await self.async_evaluate("startup")

    async def async_stop(self) -> None:
        """Stop input tracking and release common runtime resources."""
        if self._remove_state_listener is not None:
            self._remove_state_listener()
            self._remove_state_listener = None
        await super().async_stop()

    @property
    def effective_profile(self) -> PresenceLightingProfile:
        """Return the currently selected profile."""
        return self._effective_profile

    def signal_quality(self, role: str) -> SignalQuality:
        """Return the latest quality for one input role."""
        return self._signal_quality[role]

    async def async_enabled_changed(self) -> None:
        """Re-evaluate immediately after the user enables or disables control."""
        await self.async_evaluate("enabled_changed")

    async def async_set_illuminance_threshold(self, value: float) -> None:
        """Update the low-light threshold and re-evaluate the entry snapshot."""
        value = float(value)
        if self.illuminance_threshold == value:
            return
        self.illuminance_threshold = value
        if self._entry_illuminance is not None:
            self._occupied_day_profile = (
                PresenceLightingProfile.OCCUPIED_DARK
                if self._entry_illuminance <= value
                else PresenceLightingProfile.OCCUPIED_BRIGHT
            )
        await self.async_evaluate("illuminance_threshold_changed")
        self._notify_listeners()

    @callback
    def _async_input_changed(self, event: Event[EventStateChangedData]) -> None:
        """Schedule one serialized evaluation after an input state changes."""
        self.hass.async_create_task(
            self.async_evaluate(f"{event.data['entity_id']}_changed")
        )

    async def async_evaluate(self, reason: str) -> None:
        """Select an effective profile and apply only a real transition."""
        async with self._evaluate_lock:
            profile, selection_reason = self._select_profile()
            previous = self._effective_profile
            if profile is previous:
                self._log_verbose(
                    "Adaptive Control %s kept profile %s after %s",
                    self.entry.title,
                    profile,
                    reason,
                )
                return

            self._effective_profile = profile
            details = {
                "previous_profile": previous,
                "profile": profile,
                "trigger": reason,
            }
            if profile is PresenceLightingProfile.INPUT_UNAVAILABLE:
                self.record_decision("input_unavailable", selection_reason, details)
                return
            if profile is PresenceLightingProfile.DISABLED:
                self._notify_listeners()
                return

            self.record_decision("profile_selected", selection_reason, details)
            await self._async_apply_profile(previous, profile)

    def _select_profile(self) -> tuple[PresenceLightingProfile, str]:
        """Derive a profile and update quality for every input role."""
        occupancy, occupancy_quality = self._read_occupancy()
        night, night_quality = self._read_night()
        illuminance, illuminance_quality = self._read_illuminance()
        self._update_signal_quality(
            occupancy=occupancy_quality,
            night=night_quality,
            illuminance=illuminance_quality,
        )

        if not self.enabled:
            self._entry_illuminance = None
            self._occupied_day_profile = None
            return PresenceLightingProfile.DISABLED, "controller_disabled"
        if occupancy_quality is not SignalQuality.VALID:
            return PresenceLightingProfile.INPUT_UNAVAILABLE, "occupancy_unavailable"
        if occupancy is False:
            self._entry_illuminance = None
            self._occupied_day_profile = None
            return PresenceLightingProfile.VACANT, "vacancy_detected"
        if night_quality is not SignalQuality.VALID:
            return PresenceLightingProfile.INPUT_UNAVAILABLE, "night_unavailable"
        if night:
            self._entry_illuminance = None
            self._occupied_day_profile = None
            return PresenceLightingProfile.OCCUPIED_NIGHT, "night_presence_detected"
        if self._occupied_day_profile is not None:
            return self._occupied_day_profile, "occupied_day_profile_retained"
        if illuminance_quality is not SignalQuality.VALID:
            return PresenceLightingProfile.INPUT_UNAVAILABLE, "illuminance_unavailable"
        self._entry_illuminance = illuminance
        if illuminance is not None and illuminance <= self.illuminance_threshold:
            self._occupied_day_profile = PresenceLightingProfile.OCCUPIED_DARK
            return self._occupied_day_profile, "low_entry_illuminance"
        self._occupied_day_profile = PresenceLightingProfile.OCCUPIED_BRIGHT
        return self._occupied_day_profile, "sufficient_entry_illuminance"

    def _read_occupancy(self) -> tuple[bool | None, SignalQuality]:
        """Read an on/off occupancy signal."""
        state = self.hass.states.get(self.occupancy_entity_id)
        if state is None or state.state in (STATE_UNAVAILABLE, STATE_UNKNOWN):
            return None, SignalQuality.UNAVAILABLE
        if state.state == STATE_ON:
            return True, SignalQuality.VALID
        if state.state == STATE_OFF:
            return False, SignalQuality.VALID
        return None, SignalQuality.INVALID

    def _read_night(self) -> tuple[bool | None, SignalQuality]:
        """Read a sun state or a reusable on/off night context."""
        state = self.hass.states.get(self.night_entity_id)
        if state is None or state.state in (STATE_UNAVAILABLE, STATE_UNKNOWN):
            return None, SignalQuality.UNAVAILABLE
        if state.state == "below_horizon":
            return True, SignalQuality.VALID
        if state.state == "above_horizon":
            return False, SignalQuality.VALID
        if state.state == STATE_ON:
            return True, SignalQuality.VALID
        if state.state == STATE_OFF:
            return False, SignalQuality.VALID
        return None, SignalQuality.INVALID

    def _read_illuminance(self) -> tuple[float | None, SignalQuality]:
        """Read a finite non-negative illuminance measurement."""
        state = self.hass.states.get(self.illuminance_entity_id)
        if state is None or state.state in (STATE_UNAVAILABLE, STATE_UNKNOWN):
            return None, SignalQuality.UNAVAILABLE
        try:
            value = float(state.state)
        except ValueError:
            return None, SignalQuality.INVALID
        if not math.isfinite(value) or value < 0:
            return None, SignalQuality.INVALID
        return value, SignalQuality.VALID

    @callback
    def _update_signal_quality(self, **quality: SignalQuality) -> None:
        """Publish signal quality changes to diagnostic entities."""
        if quality == self._signal_quality:
            return
        self._signal_quality = quality
        self._notify_listeners()

    async def _async_apply_profile(
        self,
        previous: PresenceLightingProfile,
        profile: PresenceLightingProfile,
    ) -> None:
        """Apply stateful main-light output and one transition scene."""
        main_on = profile is PresenceLightingProfile.OCCUPIED_DARK
        await self._async_set_main_light(main_on)

        previous_scene = self._scene_for_profile(previous)
        scene = self._scene_for_profile(profile)
        if scene is not None and scene != previous_scene:
            await self._async_activate_scene(scene)

    def _scene_for_profile(self, profile: PresenceLightingProfile) -> str | None:
        """Return the transition action associated with a profile."""
        if profile is PresenceLightingProfile.VACANT:
            return self.vacant_scene_entity_id
        if profile in (
            PresenceLightingProfile.OCCUPIED_BRIGHT,
            PresenceLightingProfile.OCCUPIED_DARK,
        ):
            return self.day_scene_entity_id
        if profile is PresenceLightingProfile.OCCUPIED_NIGHT:
            return self.night_scene_entity_id
        return None

    async def _async_set_main_light(self, turn_on: bool) -> None:
        """Set the main actuator only when its current state differs."""
        state = self.hass.states.get(self.main_light_entity_id)
        desired_state = STATE_ON if turn_on else STATE_OFF
        if state is not None and state.state == desired_state:
            return
        if state is None or state.state == STATE_UNAVAILABLE:
            self._command_failed(
                self.main_light_entity_id,
                "actuator_unavailable",
            )
            return
        domain = self.main_light_entity_id.partition(".")[0]
        service = SERVICE_TURN_ON if turn_on else SERVICE_TURN_OFF
        await self._async_call(domain, service, self.main_light_entity_id)

    async def _async_activate_scene(self, entity_id: str) -> None:
        """Run one profile transition scene when it is available."""
        state = self.hass.states.get(entity_id)
        if state is None or state.state == STATE_UNAVAILABLE:
            self._command_failed(entity_id, "transition_action_unavailable")
            return
        await self._async_call("scene", SERVICE_TURN_ON, entity_id)

    async def _async_call(self, domain: str, service: str, entity_id: str) -> None:
        """Issue one observed Home Assistant service call."""
        self._log_verbose(
            "Adaptive Control %s calling %s.%s for %s",
            self.entry.title,
            domain,
            service,
            entity_id,
        )
        try:
            await self.hass.services.async_call(
                domain,
                service,
                {ATTR_ENTITY_ID: entity_id},
                blocking=True,
            )
        except (HomeAssistantError, TimeoutError, ConnectionError) as err:
            self._command_failed(entity_id, type(err).__name__)

    def _command_failed(self, entity_id: str, reason: str) -> None:
        """Record a failed command without exposing full entity state."""
        _LOGGER.warning(
            "Adaptive Control %s could not command %s: %s",
            self.entry.title,
            entity_id,
            reason,
        )
        self.record_decision(
            "command_failed",
            reason,
            {"entity_id": entity_id, "profile": self._effective_profile},
        )

    def diagnostics(self) -> dict[str, Any]:
        """Return common and Presence Lighting diagnostics."""
        return super().diagnostics() | {
            "effective_profile": self._effective_profile,
            "signal_quality": self._signal_quality,
            "illuminance_threshold": self.illuminance_threshold,
            "entry_illuminance": self._entry_illuminance,
            "bindings": {
                "occupancy": self.occupancy_entity_id,
                "illuminance": self.illuminance_entity_id,
                "night": self.night_entity_id,
                "main_light": self.main_light_entity_id,
                "day_scene": self.day_scene_entity_id,
                "night_scene": self.night_scene_entity_id,
                "vacant_scene": self.vacant_scene_entity_id,
            },
        }
