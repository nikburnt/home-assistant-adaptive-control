"""Diagnostics support for Adaptive Control."""

from typing import Any

from homeassistant.config_entries import ConfigEntry
from homeassistant.core import HomeAssistant

from .runtime import AdaptiveRuntime


async def async_get_config_entry_diagnostics(
    hass: HomeAssistant, entry: ConfigEntry
) -> dict[str, Any]:
    """Return credentials-free diagnostics for one runtime entry."""
    runtime: AdaptiveRuntime = entry.runtime_data
    return {
        "entry": {
            "title": entry.title,
            "version": entry.version,
        },
        "runtime": runtime.diagnostics(),
    }
