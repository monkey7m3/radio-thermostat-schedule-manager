"""Home Assistant setup for Radio Thermostat Schedule Manager."""

from __future__ import annotations

import logging

from homeassistant.config_entries import ConfigEntry
from homeassistant.const import CONF_HOST, Platform
from homeassistant.core import HomeAssistant

from .api import RadioThermostatApi
from .const import DOMAIN, PROFILE_KEYS, STORAGE_KEY_PREFIX, STORAGE_VERSION

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

    hass.data[DOMAIN][entry.entry_id] = {
        "api": api,
        "store": store,
        "profiles": profiles,
        "active_profile": saved.get("active_profile"),
        "last_activation": saved.get("last_activation"),
    }

    async def save_state() -> None:
        """Persist profile data and activation bookkeeping."""
        await store.async_save(
            {
                "profiles": profiles,
                "active_profile": hass.data[DOMAIN][entry.entry_id]["active_profile"],
                "last_activation": hass.data[DOMAIN][entry.entry_id]["last_activation"],
            }
        )

    hass.data[DOMAIN][entry.entry_id]["save_state"] = save_state

    # No schedule is uploaded at startup. A restart must never activate a profile.
    return True


async def async_unload_entry(
    hass: HomeAssistant, entry: RadioThermostatScheduleManagerConfigEntry
) -> bool:
    """Unload the integration."""
    hass.data.get(DOMAIN, {}).pop(entry.entry_id, None)
    return True
