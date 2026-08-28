"""Typed runtime models for Adaptive Control."""

from __future__ import annotations

from dataclasses import dataclass
from enum import StrEnum
from typing import Any


class EntryKind(StrEnum):
    """Kind of independently configured Adaptive Control runtime."""

    CONTROLLER = "controller"
    SIGNAL_PROVIDER = "signal_provider"


class SignalQuality(StrEnum):
    """Controller-visible validity of one input value."""

    VALID = "valid"
    UNAVAILABLE = "unavailable"
    INVALID = "invalid"
    STALE = "stale"


@dataclass(frozen=True, slots=True)
class Decision:
    """One bounded diagnostic decision record."""

    decision_id: str
    timestamp: str
    event: str
    reason: str
    details: dict[str, Any]

    def as_dict(self) -> dict[str, Any]:
        """Return a diagnostics-safe representation."""
        return {
            "decision_id": self.decision_id,
            "timestamp": self.timestamp,
            "event": self.event,
            "reason": self.reason,
            "details": self.details,
        }
