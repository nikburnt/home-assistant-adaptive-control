"""Shared entity helpers for Adaptive Control."""

from homeassistant.config_entries import ConfigEntry
from homeassistant.const import CONF_NAME
from homeassistant.helpers.device_registry import DeviceInfo

from .const import DOMAIN
from .runtime import AdaptiveRuntime


def entry_device_info(
    entry: ConfigEntry,
    runtime: AdaptiveRuntime,
) -> DeviceInfo:
    """Return the logical device shared by one runtime entry's entities."""
    return DeviceInfo(
        identifiers={(DOMAIN, entry.entry_id)},
        name=entry.data.get(CONF_NAME, entry.title),
        manufacturer="Adaptive Control",
        model=runtime.type_id,
    )
