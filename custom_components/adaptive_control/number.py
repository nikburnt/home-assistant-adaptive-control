"""Configuration numbers for Adaptive Control."""

from homeassistant.components.number import NumberEntity, NumberMode
from homeassistant.config_entries import ConfigEntry
from homeassistant.const import LIGHT_LUX, EntityCategory
from homeassistant.core import HomeAssistant
from homeassistant.helpers.entity_platform import AddConfigEntryEntitiesCallback

from .const import (
    CONF_ILLUMINANCE_THRESHOLD,
    ILLUMINANCE_THRESHOLD_STEP,
    MAX_ILLUMINANCE_THRESHOLD,
    MIN_ILLUMINANCE_THRESHOLD,
)
from .entity import entry_device_info
from .presence_lighting import PresenceLightingRuntime


async def async_setup_entry(
    hass: HomeAssistant,
    entry: ConfigEntry,
    async_add_entities: AddConfigEntryEntitiesCallback,
) -> None:
    """Set up configuration numbers for one typed runtime."""
    runtime = entry.runtime_data
    if not isinstance(runtime, PresenceLightingRuntime):
        return
    async_add_entities([AdaptiveIlluminanceThresholdNumber(entry, runtime)])


class AdaptiveIlluminanceThresholdNumber(NumberEntity):
    """Set the illuminance at which the main light becomes necessary."""

    _attr_entity_category = EntityCategory.CONFIG
    _attr_has_entity_name = True
    _attr_mode = NumberMode.BOX
    _attr_native_max_value = MAX_ILLUMINANCE_THRESHOLD
    _attr_native_min_value = MIN_ILLUMINANCE_THRESHOLD
    _attr_native_step = ILLUMINANCE_THRESHOLD_STEP
    _attr_native_unit_of_measurement = LIGHT_LUX
    _attr_should_poll = False
    _attr_translation_key = "illuminance_threshold"

    def __init__(
        self,
        entry: ConfigEntry,
        runtime: PresenceLightingRuntime,
    ) -> None:
        """Initialize the threshold setting."""
        self._attr_unique_id = f"{entry.entry_id}_illuminance_threshold"
        self._attr_device_info = entry_device_info(entry, runtime)
        self._entry = entry
        self._runtime = runtime

    @property
    def native_value(self) -> float:
        """Return the active low-light threshold."""
        return self._runtime.illuminance_threshold

    async def async_added_to_hass(self) -> None:
        """Subscribe to runtime updates."""
        self.async_on_remove(
            self._runtime.async_add_listener(self.async_write_ha_state)
        )

    async def async_set_native_value(self, value: float) -> None:
        """Apply and persist a new low-light threshold."""
        await self._runtime.async_set_illuminance_threshold(value)
        self.hass.config_entries.async_update_entry(
            self._entry,
            data={**self._entry.data, CONF_ILLUMINANCE_THRESHOLD: float(value)},
        )
