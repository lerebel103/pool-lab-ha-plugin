"""Base entity helpers for Pool Lab integration."""

from __future__ import annotations

from homeassistant.config_entries import ConfigEntry
from homeassistant.const import CONF_HOST
from homeassistant.helpers.device_registry import DeviceInfo

from .const import DOMAIN


def build_device_info(entry: ConfigEntry) -> DeviceInfo:
    """Build the shared device info dict for all Pool Lab entities.

    Uses entry.unique_id (host:port) as the stable device identifier
    so that the device registry entry is preserved across re-configurations.

    Note: CONF_HOST == "host", so this is compatible with existing config entries.
    """
    return DeviceInfo(
        identifiers={(DOMAIN, entry.unique_id or entry.entry_id)},
        name=f"Pool Lab ({entry.data[CONF_HOST]})",
        manufacturer="lerebel103",
        model="PL MAX Series",
    )
