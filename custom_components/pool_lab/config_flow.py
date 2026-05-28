"""Config flow for Pool Lab integration."""

from __future__ import annotations

import logging
from typing import Any

import voluptuous as vol
from homeassistant.config_entries import ConfigFlow, ConfigFlowResult
from homeassistant.const import CONF_HOST, CONF_PORT

from .client import PoolLabClient
from .const import DEFAULT_PORT, DOMAIN

_LOGGER = logging.getLogger(__name__)

STEP_USER_DATA_SCHEMA = vol.Schema(
    {
        vol.Required(CONF_HOST): str,
        vol.Optional(CONF_PORT, default=DEFAULT_PORT): int,
    }
)


class PoolLabConfigFlow(ConfigFlow, domain=DOMAIN):
    """Handle a config flow for Pool Lab."""

    VERSION = 1

    async def async_step_user(self, user_input: dict[str, Any] | None = None) -> ConfigFlowResult:
        """Handle the initial step."""
        errors: dict[str, str] = {}

        if user_input is not None:
            host = user_input[CONF_HOST]
            port = user_input[CONF_PORT]

            # Test the connection before saving
            client = PoolLabClient(host, port)
            try:
                await client.connect()
                await client.close()
            except Exception:
                _LOGGER.exception("Failed to connect to Pool Lab device")
                errors["base"] = "cannot_connect"
            else:
                # Set unique ID based on host:port to prevent duplicates
                await self.async_set_unique_id(f"{host}:{port}")
                self._abort_if_unique_id_configured()

                return self.async_create_entry(
                    title=f"Pool Lab ({host})",
                    data={
                        "host": host,
                        "port": port,
                    },
                )

        return self.async_show_form(
            step_id="user",
            data_schema=STEP_USER_DATA_SCHEMA,
            errors=errors,
        )
