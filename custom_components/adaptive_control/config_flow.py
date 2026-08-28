"""Config flow for Adaptive Control."""

from __future__ import annotations

from typing import Any

import voluptuous as vol
from homeassistant import config_entries
from homeassistant.components.binary_sensor import BinarySensorDeviceClass
from homeassistant.components.sensor import SensorDeviceClass
from homeassistant.config_entries import ConfigFlowResult
from homeassistant.const import CONF_NAME, Platform
from homeassistant.helpers.selector import (
    AreaSelector,
    EntitySelector,
    EntitySelectorConfig,
    NumberSelector,
    NumberSelectorConfig,
    NumberSelectorMode,
    TextSelector,
)

from .const import (
    CONF_AREA_ID,
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
    DEFAULT_ILLUMINANCE_THRESHOLD,
    DOMAIN,
    TYPE_PRESENCE_LIGHTING,
)
from .models import EntryKind

_MISSING = object()


class AdaptiveControlConfigFlow(config_entries.ConfigFlow, domain=DOMAIN):
    """Configure independent typed Adaptive Control entries."""

    VERSION = 1

    async def async_step_user(
        self, user_input: dict[str, Any] | None = None
    ) -> ConfigFlowResult:
        """Configure a Presence Lighting controller."""
        errors: dict[str, str] = {}
        if user_input is not None:
            if self._actuator_is_owned(user_input[CONF_MAIN_LIGHT_ENTITY_ID]):
                errors[CONF_MAIN_LIGHT_ENTITY_ID] = "actuator_already_owned"
            else:
                return self.async_create_entry(
                    title=user_input[CONF_NAME],
                    data=self._entry_data(user_input),
                )

        return self.async_show_form(
            step_id="user",
            data_schema=self._presence_lighting_schema(user_input),
            errors=errors,
        )

    async def async_step_reconfigure(
        self, user_input: dict[str, Any] | None = None
    ) -> ConfigFlowResult:
        """Update the bindings and policy for one Presence Lighting entry."""
        entry = self._get_reconfigure_entry()
        errors: dict[str, str] = {}
        if user_input is not None:
            if self._actuator_is_owned(
                user_input[CONF_MAIN_LIGHT_ENTITY_ID], entry.entry_id
            ):
                errors[CONF_MAIN_LIGHT_ENTITY_ID] = "actuator_already_owned"
            else:
                return self.async_update_reload_and_abort(
                    entry,
                    title=user_input[CONF_NAME],
                    data=self._entry_data(user_input),
                )

        return self.async_show_form(
            step_id="reconfigure",
            data_schema=self._presence_lighting_schema(user_input or dict(entry.data)),
            errors=errors,
        )

    def _presence_lighting_schema(self, defaults: dict[str, Any] | None) -> vol.Schema:
        """Build the explicit bindings and policy form."""
        defaults = defaults or {}
        schema: dict[vol.Marker, Any] = {
            _required(
                CONF_NAME,
                defaults,
                "Presence Lighting",
            ): TextSelector(),
            _required(
                CONF_OCCUPANCY_ENTITY_ID,
                defaults,
            ): EntitySelector(
                EntitySelectorConfig(
                    domain=Platform.BINARY_SENSOR,
                    device_class=[
                        BinarySensorDeviceClass.OCCUPANCY,
                        BinarySensorDeviceClass.PRESENCE,
                        BinarySensorDeviceClass.MOTION,
                    ],
                )
            ),
            _required(
                CONF_ILLUMINANCE_ENTITY_ID,
                defaults,
            ): EntitySelector(
                EntitySelectorConfig(
                    domain=Platform.SENSOR,
                    device_class=SensorDeviceClass.ILLUMINANCE,
                )
            ),
            _required(
                CONF_NIGHT_ENTITY_ID,
                defaults,
                "sun.sun",
            ): EntitySelector(EntitySelectorConfig(domain="sun")),
            _required(
                CONF_MAIN_LIGHT_ENTITY_ID,
                defaults,
            ): EntitySelector(
                EntitySelectorConfig(domain=[Platform.LIGHT, Platform.SWITCH])
            ),
            _required(
                CONF_DAY_SCENE_ENTITY_ID,
                defaults,
            ): EntitySelector(EntitySelectorConfig(domain=Platform.SCENE)),
            _required(
                CONF_NIGHT_SCENE_ENTITY_ID,
                defaults,
            ): EntitySelector(EntitySelectorConfig(domain=Platform.SCENE)),
            _required(
                CONF_VACANT_SCENE_ENTITY_ID,
                defaults,
            ): EntitySelector(EntitySelectorConfig(domain=Platform.SCENE)),
            _required(
                CONF_ILLUMINANCE_THRESHOLD,
                defaults,
                DEFAULT_ILLUMINANCE_THRESHOLD,
            ): NumberSelector(
                NumberSelectorConfig(
                    min=0,
                    max=2000,
                    step=5,
                    unit_of_measurement="lx",
                    mode=NumberSelectorMode.BOX,
                )
            ),
            _optional(CONF_AREA_ID, defaults): AreaSelector(),
        }
        return vol.Schema(schema)

    @staticmethod
    def _entry_data(user_input: dict[str, Any]) -> dict[str, Any]:
        """Add the immutable runtime type to validated user input."""
        return dict(user_input) | {
            CONF_ENTRY_KIND: EntryKind.CONTROLLER,
            CONF_TYPE_ID: TYPE_PRESENCE_LIGHTING,
        }

    def _actuator_is_owned(
        self,
        entity_id: str,
        current_entry_id: str | None = None,
    ) -> bool:
        """Prevent two Adaptive Control entries from owning one actuator."""
        return any(
            entry.entry_id != current_entry_id
            and entry.data.get(CONF_MAIN_LIGHT_ENTITY_ID) == entity_id
            for entry in self._async_current_entries()
        )


def _required(
    key: str,
    defaults: dict[str, Any],
    fallback: Any = _MISSING,
) -> vol.Marker:
    """Return a required marker without serializing a null UI default."""
    value = defaults.get(key, fallback)
    if value is _MISSING:
        return vol.Required(key)
    return vol.Required(key, default=value)


def _optional(key: str, defaults: dict[str, Any]) -> vol.Marker:
    """Return an optional marker that preserves a configured value."""
    if key not in defaults:
        return vol.Optional(key)
    return vol.Optional(key, default=defaults[key])
