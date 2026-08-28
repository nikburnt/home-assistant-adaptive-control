"""Constants for Adaptive Control."""

from homeassistant.const import Platform

DOMAIN = "adaptive_control"

CONF_ENTRY_KIND = "entry_kind"
CONF_TYPE_ID = "type_id"

MAX_DECISION_TRACE = 50

PLATFORMS = (Platform.SWITCH,)
