"""Home Assistant setup for Radio Thermostat Schedule Manager."""

from __future__ import annotations

from datetime import datetime, timezone
import logging

from homeassistant.config_entries import ConfigEntry
from homeassistant.const import CONF_HOST
from homeassistant.core import HomeAssistant, ServiceCall
from homeassistant.exceptions import HomeAssistantError

from .api import RadioThermostatApi, RadioThermostatApiError
from .const import DOMAIN, PROFILE_KEYS, STORAGE_KEY_PREFIX, STORAGE_VERSION
from .schedule import InvalidProgram, normalize_program, programs_equal

_LOGGER = logging.getLogger(__name__)
type RadioThermostatScheduleManagerConfigEntry = ConfigEntry


async def async_setup(hass: HomeAssistant, config: dict) -> bool:
    """Set up the integration."""
    hass.data.setdefault(DOMAIN, {})
    return True


async def async_setup_entry(
    hass: HomeAssistant, entry: RadioThermostatScheduleManagerConfigEntry
) -> bool:
    """Set up a configured thermostat and initialize saved profiles."""
    from homeassistant.helpers.aiohttp_client import async_get_clientsession
    from homeassistant.helpers.storage import Store

    api = RadioThermostatApi(entry.data[CONF_HOST], async_get_clientsession(hass))
    store = Store(hass, STORAGE_VERSION, f"{STORAGE_KEY_PREFIX}_{entry.entry_id}")
    saved = await store.async_load()
    if not isinstance(saved, dict):
        saved = {}

    profiles = saved.get("profiles")
    if not isinstance(profiles, dict):
        profiles = {}
    for key in PROFILE_KEYS:
        profiles.setdefault(key, None)

    runtime = {
        "api": api,
        "store": store,
        "profiles": profiles,
        "active_profile": saved.get("active_profile"),
        "last_activation": saved.get("last_activation"),
        "last_activation_result": saved.get("last_activation_result"),
    }
    hass.data[DOMAIN][entry.entry_id] = runtime

    async def save_state() -> None:
        """Persist profile data and activation bookkeeping."""
        await store.async_save(
            {
                "profiles": runtime["profiles"],
                "active_profile": runtime["active_profile"],
                "last_activation": runtime["last_activation"],
                "last_activation_result": runtime["last_activation_result"],
            }
        )

    runtime["save_state"] = save_state

    async def handle_save_profile(call: ServiceCall) -> None:
        """Save a profile in Home Assistant only; do not upload it."""
        target_id = call.data.get("entry_id", entry.entry_id)
        target = hass.data[DOMAIN].get(target_id)
        if target is None:
            raise HomeAssistantError("Unknown Radio Thermostat Schedule Manager entry")
        profile = call.data["profile"]
        if profile not in PROFILE_KEYS:
            raise HomeAssistantError(f"Unknown profile: {profile}")
        try:
            program = normalize_program(call.data["program"])
        except (InvalidProgram, TypeError) as err:
            raise HomeAssistantError(f"Invalid weekly program: {err}") from err
        target["profiles"][profile] = program
        await target["save_state"]()

    async def handle_activate_profile(call: ServiceCall) -> None:
        """Upload a Home/Away heat and cool pair, then verify both by reading back."""
        target_id = call.data.get("entry_id", entry.entry_id)
        target = hass.data[DOMAIN].get(target_id)
        if target is None:
            raise HomeAssistantError("Unknown Radio Thermostat Schedule Manager entry")

        choice = call.data["profile"]
        if choice not in ("home", "away"):
            raise HomeAssistantError("Profile must be 'home' or 'away'")
        heat_key, cool_key = f"{choice}_heat", f"{choice}_cool"
        heat = target["profiles"].get(heat_key)
        cool = target["profiles"].get(cool_key)
        if heat is None or cool is None:
            raise HomeAssistantError(
                f"Both {heat_key} and {cool_key} must be saved before activation"
            )

        # Validate both schedules before changing either thermostat program.
        try:
            heat = normalize_program(heat)
            cool = normalize_program(cool)
        except (InvalidProgram, TypeError) as err:
            raise HomeAssistantError(f"Saved profile is invalid: {err}") from err

        api: RadioThermostatApi = target["api"]
        result = {"heat": "not_attempted", "cool": "not_attempted"}
        try:
            async with api.lock:
                status_before = await api.get_status()
                mode_before = status_before.get("tmode")
                for mode, program in (("heat", heat), ("cool", cool)):
                    try:
                        await api.set_program(mode, program)
                        result[mode] = "written_unverified"
                        actual = await api.get_program(mode)
                        if not programs_equal(program, actual):
                            result[mode] = "readback_mismatch"
                            raise RadioThermostatApiError(
                                f"{mode} schedule readback did not match the saved profile"
                            )
                        result[mode] = "verified"
                    except Exception:
                        result[mode] = "failed"
                        raise
                status_after = await api.get_status()
                if status_after.get("tmode") != mode_before:
                    raise RadioThermostatApiError(
                        "Thermostat operating mode changed during schedule activation"
                    )
        except Exception as err:
            target["last_activation_result"] = {
                "profile": choice,
                "time": datetime.now(timezone.utc).isoformat(),
                "result": result,
                "error": str(err),
            }
            await target["save_state"]()
            raise HomeAssistantError(
                "Schedule activation was not fully verified. "
                f"Heat: {result['heat']}; Cool: {result['cool']}. Details: {err}"
            ) from err

        now = datetime.now(timezone.utc).isoformat()
        target["active_profile"] = choice
        target["last_activation"] = now
        target["last_activation_result"] = {
            "profile": choice,
            "time": now,
            "result": result,
            "error": None,
        }
        await target["save_state"]()

    # Services are registered once and dispatch to the selected config entry.
    if not hass.services.has_service(DOMAIN, "save_profile"):
        hass.services.async_register(DOMAIN, "save_profile", handle_save_profile)
    if not hass.services.has_service(DOMAIN, "activate_profile"):
        hass.services.async_register(DOMAIN, "activate_profile", handle_activate_profile)

    # No schedule is uploaded at setup or Home Assistant restart.
    return True


async def async_unload_entry(
    hass: HomeAssistant, entry: RadioThermostatScheduleManagerConfigEntry
) -> bool:
    """Unload the integration."""
    hass.data.get(DOMAIN, {}).pop(entry.entry_id, None)
    if not hass.data.get(DOMAIN):
        hass.services.async_remove(DOMAIN, "save_profile")
        hass.services.async_remove(DOMAIN, "activate_profile")
    return True
