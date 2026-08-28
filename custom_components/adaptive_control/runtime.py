"""Shared runtime foundation for Controllers and Signal Providers."""

from __future__ import annotations

import logging
from collections import deque
from collections.abc import Callable, Mapping
from typing import Any
from uuid import uuid4

from homeassistant.config_entries import ConfigEntry
from homeassistant.core import HomeAssistant, callback
from homeassistant.util import dt as dt_util

from .const import CONF_ENTRY_KIND, CONF_TYPE_ID, MAX_DECISION_TRACE
from .models import Decision, EntryKind

_LOGGER = logging.getLogger(__name__)

Listener = Callable[[], None]


class AdaptiveRuntime:
    """Common lifecycle and observability for one runtime entry."""

    def __init__(self, hass: HomeAssistant, entry: ConfigEntry) -> None:
        """Initialize a Controller or Signal Provider runtime."""
        self.hass = hass
        self.entry = entry
        self.kind = EntryKind(entry.data[CONF_ENTRY_KIND])
        self.type_id = str(entry.data[CONF_TYPE_ID])
        self._listeners: set[Listener] = set()
        self._decision_trace: deque[Decision] = deque(maxlen=MAX_DECISION_TRACE)
        self._verbose_logging_enabled = False

    async def async_start(self) -> None:
        """Start the runtime foundation."""
        self._log_verbose(
            "Adaptive Control %s started %s type %s",
            self.entry.title,
            self.kind,
            self.type_id,
        )

    async def async_stop(self) -> None:
        """Stop the runtime foundation."""
        self._listeners.clear()

    @callback
    def async_add_listener(self, listener: Listener) -> Callable[[], None]:
        """Subscribe an entity to runtime updates."""
        self._listeners.add(listener)
        return lambda: self._listeners.discard(listener)

    @callback
    def _notify_listeners(self) -> None:
        """Notify all entities owned by this runtime."""
        for listener in tuple(self._listeners):
            listener()

    @property
    def verbose_logging_enabled(self) -> bool:
        """Return whether detailed logs are promoted for this entry."""
        return self._verbose_logging_enabled

    @callback
    def async_set_verbose_logging(self, enabled: bool) -> None:
        """Enable or disable detailed logs for this entry."""
        if self._verbose_logging_enabled == enabled:
            return
        self._verbose_logging_enabled = enabled
        _LOGGER.info(
            "Verbose logging %s for Adaptive Control %s",
            "enabled" if enabled else "disabled",
            self.entry.title,
        )
        self._notify_listeners()

    def _log_verbose(self, message: str, *args: Any) -> None:
        """Log details at INFO only when this entry opts in."""
        log = _LOGGER.info if self._verbose_logging_enabled else _LOGGER.debug
        log(message, *args)

    @callback
    def record_decision(
        self,
        event: str,
        reason: str,
        details: Mapping[str, Any] | None = None,
    ) -> Decision:
        """Append one bounded decision record and return its correlation data."""
        decision = Decision(
            decision_id=uuid4().hex,
            timestamp=dt_util.utcnow().isoformat(),
            event=event,
            reason=reason,
            details=dict(details or {}),
        )
        self._decision_trace.append(decision)
        self._log_verbose(
            "Adaptive Control %s recorded decision %s: %s after %s",
            self.entry.title,
            decision.decision_id,
            event,
            reason,
        )
        self._notify_listeners()
        return decision

    @property
    def decision_trace(self) -> tuple[Decision, ...]:
        """Return the bounded decision trace in chronological order."""
        return tuple(self._decision_trace)

    def diagnostics(self) -> dict[str, Any]:
        """Return credentials-free common runtime diagnostics."""
        return {
            "entry_kind": self.kind,
            "type_id": self.type_id,
            "verbose_logging_enabled": self._verbose_logging_enabled,
            "decision_trace": [decision.as_dict() for decision in self._decision_trace],
        }
