"""The Pool Lab integration."""

from __future__ import annotations

import logging

from homeassistant.config_entries import ConfigEntry
from homeassistant.const import Platform
from homeassistant.core import HomeAssistant

from .client import PoolLabClient
from .const import DOMAIN
from .coordinator import PoolLabCoordinator

_LOGGER = logging.getLogger(__name__)

PLATFORMS: list[Platform] = [
    Platform.SENSOR,
    Platform.BINARY_SENSOR,
    Platform.SWITCH,
    Platform.NUMBER,
]

PoolLabConfigEntry = ConfigEntry


async def async_setup_entry(hass: HomeAssistant, entry: PoolLabConfigEntry) -> bool:
    """Set up Pool Lab from a config entry."""
    host = entry.data["host"]
    port = entry.data["port"]

    client = PoolLabClient(host, port)

    try:
        await client.connect()
    except ConnectionError as err:
        _LOGGER.error("Failed to connect to Pool Lab device at %s:%s: %s", host, port, err)
        return False

    coordinator = PoolLabCoordinator(hass, client)

    # Use the initial status from the handshake for the first update
    if client.initial_status:
        coordinator.set_initial_status(client.initial_status)

    # Perform the first data fetch
    await coordinator.async_config_entry_first_refresh()

    hass.data.setdefault(DOMAIN, {})
    hass.data[DOMAIN][entry.entry_id] = coordinator

    await hass.config_entries.async_forward_entry_setups(entry, PLATFORMS)

    return True


async def async_unload_entry(hass: HomeAssistant, entry: PoolLabConfigEntry) -> bool:
    """Unload a config entry."""
    unload_ok = await hass.config_entries.async_unload_platforms(entry, PLATFORMS)

    if unload_ok:
        coordinator: PoolLabCoordinator = hass.data[DOMAIN].pop(entry.entry_id)
        await coordinator.client.close()

    return unload_ok
