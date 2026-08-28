"""Set up Adaptive Control."""

from homeassistant.config_entries import ConfigEntry
from homeassistant.core import HomeAssistant
from homeassistant.helpers import device_registry as dr

from .const import CONF_AREA_ID, DOMAIN, PLATFORMS
from .runtime import AdaptiveRuntime, create_runtime


async def async_setup_entry(hass: HomeAssistant, entry: ConfigEntry) -> bool:
    """Set up one Controller or Signal Provider entry."""
    runtime = create_runtime(hass, entry)
    entry.runtime_data = runtime
    await runtime.async_start()
    await hass.config_entries.async_forward_entry_setups(entry, PLATFORMS)
    if area_id := entry.data.get(CONF_AREA_ID):
        registry = dr.async_get(hass)
        if device := registry.async_get_device(identifiers={(DOMAIN, entry.entry_id)}):
            registry.async_update_device(device.id, area_id=area_id)
    return True


async def async_unload_entry(hass: HomeAssistant, entry: ConfigEntry) -> bool:
    """Unload one Controller or Signal Provider entry."""
    if not await hass.config_entries.async_unload_platforms(entry, PLATFORMS):
        return False
    runtime: AdaptiveRuntime = entry.runtime_data
    await runtime.async_stop()
    return True
