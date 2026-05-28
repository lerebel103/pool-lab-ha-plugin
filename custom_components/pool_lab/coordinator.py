"""Data update coordinator for Pool Lab devices.

The coordinator manages the TCP connection lifecycle, polls for status
updates, and provides the parsed device state to all entities.
"""

from __future__ import annotations

import logging
from datetime import timedelta

from homeassistant.core import HomeAssistant
from homeassistant.helpers.update_coordinator import DataUpdateCoordinator, UpdateFailed

from .client import PoolLabClient
from .const import DOMAIN
from .models import PoolLabState
from .protocol import cmd_status_request, parse_status_update

_LOGGER = logging.getLogger(__name__)

UPDATE_INTERVAL = timedelta(seconds=30)


class PoolLabCoordinator(DataUpdateCoordinator[PoolLabState]):
    """Coordinator that manages communication with a Pool Lab device.

    Maintains the TCP connection, polls for status updates, and
    exposes the latest parsed state to all platform entities.
    """

    def __init__(self, hass: HomeAssistant, client: PoolLabClient) -> None:
        """Initialize the coordinator."""
        super().__init__(
            hass,
            _LOGGER,
            name=f"{DOMAIN}_{client.host}",
            update_interval=UPDATE_INTERVAL,
        )
        self.client = client
        self._initial_status: str | None = None

    def set_initial_status(self, raw_status: str) -> None:
        """Store the initial status received during connection handshake.

        The device sends a status update immediately after 'connected'.
        This avoids an extra poll on first load.
        """
        self._initial_status = raw_status

    async def _async_update_data(self) -> PoolLabState:
        """Fetch the latest state from the device.

        On the first call, uses the initial status from the handshake.
        Subsequent calls send the 'up;' command to request a fresh update.
        """
        # Use initial status if available (first poll after connect)
        if self._initial_status is not None:
            raw = self._initial_status
            self._initial_status = None
            return parse_status_update(raw)

        # Ensure we're connected
        if not self.client.connected:
            try:
                await self.client.connect()
            except ConnectionError as err:
                raise UpdateFailed(f"Cannot reconnect to device: {err}") from err

        # Request a status update
        try:
            raw = await self.client.send_command(cmd_status_request())
        except ConnectionError as err:
            raise UpdateFailed(f"Communication error: {err}") from err

        return parse_status_update(raw)

    async def async_send_command(self, command: str) -> None:
        """Send a command to the device and trigger a state refresh.

        Used by entity platforms to issue control commands.
        After sending, requests a fresh status update to sync state.
        """
        if not self.client.connected:
            try:
                await self.client.connect()
            except ConnectionError as err:
                raise UpdateFailed(f"Cannot reconnect to device: {err}") from err

        try:
            await self.client.send_command(command)
        except ConnectionError as err:
            raise UpdateFailed(f"Failed to send command: {err}") from err

        # Request immediate refresh
        await self.async_request_refresh()
