"""Configuration switches for Adaptive Control."""

from homeassistant.components.switch import SwitchEntity
from homeassistant.config_entries import ConfigEntry
from homeassistant.const import STATE_ON, EntityCategory
from homeassistant.core import HomeAssistant
from homeassistant.helpers.entity_platform import AddConfigEntryEntitiesCallback
from homeassistant.helpers.restore_state import RestoreEntity

from .entity import entry_device_info
from .runtime import AdaptiveRuntime


async def async_setup_entry(
    hass: HomeAssistant,
    entry: ConfigEntry,
    async_add_entities: AddConfigEntryEntitiesCallback,
) -> None:
    """Set up configuration switches for one runtime entry."""
    async_add_entities([AdaptiveVerboseLoggingSwitch(entry, entry.runtime_data)])


class AdaptiveVerboseLoggingSwitch(SwitchEntity, RestoreEntity):
    """Enable detailed runtime logs for one Adaptive Control entry."""

    _attr_entity_category = EntityCategory.CONFIG
    _attr_has_entity_name = True
    _attr_should_poll = False
    _attr_translation_key = "verbose_logging"

    def __init__(
        self,
        entry: ConfigEntry,
        runtime: AdaptiveRuntime,
    ) -> None:
        """Initialize the verbose logging switch."""
        self._attr_unique_id = f"{entry.entry_id}_verbose_logging"
        self._attr_device_info = entry_device_info(entry, runtime)
        self._runtime = runtime

    @property
    def is_on(self) -> bool:
        """Return whether detailed logs are enabled for this entry."""
        return self._runtime.verbose_logging_enabled

    async def async_added_to_hass(self) -> None:
        """Restore the setting and subscribe to runtime updates."""
        await super().async_added_to_hass()
        if (last_state := await self.async_get_last_state()) is not None:
            self._runtime.async_set_verbose_logging(last_state.state == STATE_ON)
        self.async_on_remove(
            self._runtime.async_add_listener(self.async_write_ha_state)
        )

    async def async_turn_on(self, **kwargs) -> None:
        """Enable detailed logs for this entry."""
        self._runtime.async_set_verbose_logging(True)

    async def async_turn_off(self, **kwargs) -> None:
        """Disable detailed logs for this entry."""
        self._runtime.async_set_verbose_logging(False)
