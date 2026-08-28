"""State and signal-quality sensors for Adaptive Control."""

from collections.abc import Callable

from homeassistant.components.sensor import SensorDeviceClass, SensorEntity
from homeassistant.config_entries import ConfigEntry
from homeassistant.core import HomeAssistant
from homeassistant.helpers.entity_platform import AddConfigEntryEntitiesCallback

from .entity import entry_device_info
from .models import SignalQuality
from .presence_lighting import PresenceLightingProfile, PresenceLightingRuntime


async def async_setup_entry(
    hass: HomeAssistant,
    entry: ConfigEntry,
    async_add_entities: AddConfigEntryEntitiesCallback,
) -> None:
    """Set up state sensors for one typed runtime."""
    runtime = entry.runtime_data
    if not isinstance(runtime, PresenceLightingRuntime):
        return
    async_add_entities(
        [
            AdaptiveRuntimeSensor(
                entry,
                runtime,
                "effective_profile",
                lambda: runtime.effective_profile,
                [profile.value for profile in PresenceLightingProfile],
            ),
            AdaptiveRuntimeSensor(
                entry,
                runtime,
                "occupancy_quality",
                lambda: runtime.signal_quality("occupancy"),
                [quality.value for quality in SignalQuality],
            ),
            AdaptiveRuntimeSensor(
                entry,
                runtime,
                "illuminance_quality",
                lambda: runtime.signal_quality("illuminance"),
                [quality.value for quality in SignalQuality],
            ),
            AdaptiveRuntimeSensor(
                entry,
                runtime,
                "night_quality",
                lambda: runtime.signal_quality("night"),
                [quality.value for quality in SignalQuality],
            ),
        ]
    )


class AdaptiveRuntimeSensor(SensorEntity):
    """Expose one observable value from a typed runtime."""

    _attr_device_class = SensorDeviceClass.ENUM
    _attr_has_entity_name = True
    _attr_should_poll = False

    def __init__(
        self,
        entry: ConfigEntry,
        runtime: PresenceLightingRuntime,
        translation_key: str,
        value: Callable[[], str],
        options: list[str],
    ) -> None:
        """Initialize one runtime sensor."""
        self._attr_unique_id = f"{entry.entry_id}_{translation_key}"
        self._attr_translation_key = translation_key
        self._attr_options = options
        self._attr_device_info = entry_device_info(entry, runtime)
        self._runtime = runtime
        self._value = value

    @property
    def native_value(self) -> str:
        """Return the current runtime value."""
        return self._value()

    async def async_added_to_hass(self) -> None:
        """Subscribe to runtime updates."""
        self.async_on_remove(
            self._runtime.async_add_listener(self.async_write_ha_state)
        )
