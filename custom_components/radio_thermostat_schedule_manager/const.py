"""Constants for Radio Thermostat Schedule Manager."""

DOMAIN = "radio_thermostat_schedule_manager"
PLATFORMS = []
CONF_HOST = "host"
DEFAULT_SCAN_INTERVAL = 6 * 60 * 60
DEFAULT_CLOCK_TOLERANCE_SECONDS = 120
STORAGE_VERSION = 1
STORAGE_KEY_PREFIX = "radio_thermostat_schedule_manager"

PROFILE_KEYS = (
    "home_heat",
    "away_heat",
    "home_cool",
    "away_cool",
)

PROFILE_LABELS = {
    "home_heat": "Home Heat",
    "away_heat": "Away Heat",
    "home_cool": "Home Cool",
    "away_cool": "Away Cool",
}

PROGRAM_ENDPOINTS = {
    "heat": "/tstat/program/heat",
    "cool": "/tstat/program/cool",
}
