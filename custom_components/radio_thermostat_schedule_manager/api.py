"""Minimal asynchronous CT50 API client.

The CT50 local API uses HTTP and JSON. This client deliberately keeps API
operations small and explicit so callers can serialize writes and verify them.
"""

from __future__ import annotations

import asyncio
import logging
from typing import Any

import aiohttp

_LOGGER = logging.getLogger(__name__)


class RadioThermostatApiError(Exception):
    """Raised when a thermostat request fails or returns invalid data."""


class RadioThermostatApi:
    """HTTP client for the CT50 API."""

    def __init__(self, host: str, session: aiohttp.ClientSession) -> None:
        self._base_url = f"http://{host.strip().rstrip('/')}"
        self._session = session
        self.lock = asyncio.Lock()

    async def request_json(
        self, method: str, path: str, payload: dict[str, Any] | None = None
    ) -> dict[str, Any]:
        """Send a JSON request and return a JSON object."""
        url = f"{self._base_url}{path}"
        try:
            async with self._session.request(
                method,
                url,
                json=payload,
                timeout=aiohttp.ClientTimeout(total=10),
            ) as response:
                response.raise_for_status()
                data = await response.json(content_type=None)
        except (aiohttp.ClientError, asyncio.TimeoutError, ValueError) as err:
            raise RadioThermostatApiError(
                f"Request {method} {path} failed: {err}"
            ) from err

        if not isinstance(data, dict):
            raise RadioThermostatApiError(
                f"Request {method} {path} returned a non-object JSON response"
            )
        return data

    async def get_status(self) -> dict[str, Any]:
        """Read current thermostat status."""
        return await self.request_json("GET", "/tstat")

    async def get_program(self, mode: str) -> dict[str, Any]:
        """Read a complete weekly program."""
        if mode not in ("heat", "cool"):
            raise ValueError("mode must be 'heat' or 'cool'")
        return await self.request_json("GET", f"/tstat/program/{mode}")

    async def set_program(self, mode: str, program: dict[str, list[int]]) -> None:
        """Write a complete weekly program."""
        if mode not in ("heat", "cool"):
            raise ValueError("mode must be 'heat' or 'cool'")
        await self.request_json("POST", f"/tstat/program/{mode}", program)

    async def get_clock(self) -> dict[str, Any]:
        """Read the thermostat's reported clock from its status response."""
        status = await self.get_status()
        clock = status.get("time")
        if not isinstance(clock, dict):
            raise RadioThermostatApiError("Thermostat status has no valid 'time' object")
        return clock
