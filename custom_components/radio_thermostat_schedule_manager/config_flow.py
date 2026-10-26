"""Config flow for Radio Thermostat Schedule Manager."""

from __future__ import annotations

import voluptuous as vol
from homeassistant import config_entries
from homeassistant.const import CONF_HOST
from homeassistant.core import HomeAssistant
from homeassistant.data_entry_flow import FlowResult

from .api import RadioThermostatApi, RadioThermostatApiError
from .const import DOMAIN


class RadioThermostatScheduleManagerConfigFlow(config_entries.ConfigFlow, domain=DOMAIN):
    """Handle setup via the Home Assistant UI."""

    VERSION = 1

    async def async_step_user(self, user_input: dict | None = None) -> FlowResult:
        """Ask for the thermostat host/IP and validate connectivity."""
        errors: dict[str, str] = {}
        if user_input is not None:
            host = user_input[CONF_HOST].strip()
            await self.async_set_unique_id(host.lower())
            self._abort_if_unique_id_configured()

            from homeassistant.helpers.aiohttp_client import async_get_clientsession

            api = RadioThermostatApi(host, async_get_clientsession(self.hass))
            try:
                status = await api.get_status()
                if not isinstance(status.get("temp"), (int, float)):
                    errors["base"] = "invalid_response"
                else:
                    return self.async_create_entry(
                        title=f"Radio Thermostat ({host})",
                        data={CONF_HOST: host},
                    )
            except RadioThermostatApiError:
                errors["base"] = "cannot_connect"

        schema = vol.Schema({vol.Required(CONF_HOST): str})
        return self.async_show_form(
            step_id="user",
            data_schema=schema,
            errors=errors,
            description_placeholders={
                "note": "Enter the CT50 hostname or IP address on your local network."
            },
        )
