"""Base entity helpers for Pool Lab integration."""

from __future__ import annotations

from homeassistant.config_entries import ConfigEntry
from homeassistant.const import CONF_HOST, CONF_PORT
from homeassistant.helpers.device_registry import DeviceInfo

from .const import DOMAIN


def build_device_info(entry: ConfigEntry) -> DeviceInfo:
    """Build the shared device info dict for all Pool Lab entities.

    Uses entry.unique_id (host:port) as the stable device identifier
    so that the device registry entry is preserved across re-configurations.
    Falls back to deriving host:port from entry.data if unique_id is not set.

    Note: CONF_HOST == "host" and CONF_PORT == "port", compatible with existing entries.
    """
    identifier = entry.unique_id or f"{entry.data[CONF_HOST]}:{entry.data[CONF_PORT]}"
    return DeviceInfo(
        identifiers={(DOMAIN, identifier)},
        name=f"Pool Lab ({entry.data[CONF_HOST]})",
        manufacturer="lerebel103",
        model="PL MAX Series",
    )
