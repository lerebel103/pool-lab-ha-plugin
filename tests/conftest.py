"""Shared test fixtures for Pool Lab integration tests."""

from __future__ import annotations

import asyncio
import sys
from unittest.mock import MagicMock

# Mock homeassistant and voluptuous modules so we can import our code
# without a full Home Assistant installation.
for mod in [
    "homeassistant",
    "homeassistant.components",
    "homeassistant.components.binary_sensor",
    "homeassistant.components.number",
    "homeassistant.components.select",
    "homeassistant.components.sensor",
    "homeassistant.components.switch",
    "homeassistant.config_entries",
    "homeassistant.const",
    "homeassistant.core",
    "homeassistant.helpers",
    "homeassistant.helpers.entity_platform",
    "homeassistant.helpers.update_coordinator",
    "voluptuous",
]:
    sys.modules.setdefault(mod, MagicMock())

import pytest


@pytest.fixture
def mock_device_host() -> str:
    """Return a test device host."""
    return "192.168.1.100"


@pytest.fixture
def mock_device_port() -> int:
    """Return a test device port."""
    return 8080


@pytest.fixture
def tcp_server(mock_device_host: str):
    """Factory fixture to create a TCP server that simulates a Pool Lab device.

    Returns a callable that accepts a handler coroutine and returns
    (host, port) of the running server.
    """
    servers = []

    async def _create_server(handler):
        """Create a server with the given client handler."""
        server = await asyncio.start_server(handler, "127.0.0.1", 0)
        servers.append(server)
        addr = server.sockets[0].getsockname()
        return addr[0], addr[1]

    yield _create_server

    # Cleanup
    for server in servers:
        server.close()
