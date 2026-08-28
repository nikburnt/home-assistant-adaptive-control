"""Semantic decision events for Adaptive Control."""

from typing import ClassVar

from homeassistant.components.event import EventEntity
from homeassistant.config_entries import ConfigEntry
from homeassistant.core import HomeAssistant, callback
from homeassistant.helpers.entity_platform import AddConfigEntryEntitiesCallback

from .const import DECISION_EVENT_TYPES
from .entity import entry_device_info
from .runtime import AdaptiveRuntime


async def async_setup_entry(
    hass: HomeAssistant,
    entry: ConfigEntry,
    async_add_entities: AddConfigEntryEntitiesCallback,
) -> None:
    """Set up one semantic decision event per runtime."""
    async_add_entities([AdaptiveDecisionEvent(entry, entry.runtime_data)])


class AdaptiveDecisionEvent(EventEntity):
    """Publish meaningful runtime decisions without verbose logging."""

    _attr_event_types: ClassVar[list[str]] = list(DECISION_EVENT_TYPES)
    _attr_has_entity_name = True
    _attr_should_poll = False
    _attr_translation_key = "decision"

    def __init__(self, entry: ConfigEntry, runtime: AdaptiveRuntime) -> None:
        """Initialize the decision event."""
        self._attr_unique_id = f"{entry.entry_id}_decision"
        self._attr_device_info = entry_device_info(entry, runtime)
        self._runtime = runtime
        self._last_decision_id = (
            runtime.latest_decision.decision_id if runtime.latest_decision else None
        )

    async def async_added_to_hass(self) -> None:
        """Subscribe without replaying decisions recorded before entity setup."""
        await super().async_added_to_hass()
        self._last_decision_id = (
            self._runtime.latest_decision.decision_id
            if self._runtime.latest_decision
            else None
        )
        self.async_on_remove(self._runtime.async_add_listener(self._async_updated))

    @callback
    def _async_updated(self) -> None:
        """Forward one newly recorded semantic decision."""
        decision = self._runtime.latest_decision
        if decision is None or decision.decision_id == self._last_decision_id:
            return
        self._last_decision_id = decision.decision_id
        if decision.event not in self.event_types:
            return
        self._trigger_event(
            decision.event,
            {
                "decision_id": decision.decision_id,
                "reason": decision.reason,
                **decision.details,
            },
        )
        self.async_write_ha_state()
