"""The Pool Lab integration."""

from __future__ import annotations

import logging

from homeassistant.config_entries import ConfigEntry
from homeassistant.core import HomeAssistant

from .client import PoolLabClient
from .const import DOMAIN

_LOGGER = logging.getLogger(__name__)

PoolLabConfigEntry = ConfigEntry


async def async_setup_entry(hass: HomeAssistant, entry: PoolLabConfigEntry) -> bool:
    """Set up Pool Lab from a config entry."""
    host = entry.data["host"]
    port = entry.data["port"]

    client = PoolLabClient(host, port)

    try:
        await client.connect()
    except Exception as err:
        _LOGGER.error("Failed to connect to Pool Lab device at %s:%s: %s", host, port, err)
        await client.close()
        return False

    hass.data.setdefault(DOMAIN, {})
    hass.data[DOMAIN][entry.entry_id] = client

    return True


async def async_unload_entry(hass: HomeAssistant, entry: PoolLabConfigEntry) -> bool:
    """Unload a config entry."""
    client: PoolLabClient = hass.data[DOMAIN].pop(entry.entry_id)
    await client.close()
    return True
