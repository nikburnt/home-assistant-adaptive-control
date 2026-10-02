"""Constants for Adaptive Control."""

from homeassistant.const import Platform

DOMAIN = "adaptive_control"

CONF_ENTRY_KIND = "entry_kind"
CONF_TYPE_ID = "type_id"
CONF_AREA_ID = "area_id"

TYPE_PRESENCE_LIGHTING = "presence_lighting"

CONF_OCCUPANCY_ENTITY_ID = "occupancy_entity_id"
CONF_ILLUMINANCE_ENTITY_ID = "illuminance_entity_id"
CONF_NIGHT_ENTITY_ID = "night_entity_id"
CONF_MAIN_LIGHT_ENTITY_ID = "main_light_entity_id"
CONF_DAY_SCENE_ENTITY_ID = "day_scene_entity_id"
CONF_NIGHT_SCENE_ENTITY_ID = "night_scene_entity_id"
CONF_VACANT_SCENE_ENTITY_ID = "vacant_scene_entity_id"
CONF_ILLUMINANCE_THRESHOLD = "illuminance_threshold"

DEFAULT_ILLUMINANCE_THRESHOLD = 100.0
MIN_ILLUMINANCE_THRESHOLD = 0.0
MAX_ILLUMINANCE_THRESHOLD = 2000.0
ILLUMINANCE_THRESHOLD_STEP = 5.0

MAX_DECISION_TRACE = 50

DECISION_EVENT_TYPES = (
    "controller_disabled",
    "controller_enabled",
    "input_unavailable",
    "profile_selected",
    "command_failed",
)

PLATFORMS = (Platform.EVENT, Platform.NUMBER, Platform.SENSOR, Platform.SWITCH)
