"""Shared test fixtures for Pool Lab integration tests."""

from __future__ import annotations

import sys
from unittest.mock import MagicMock

# Mock homeassistant and voluptuous modules so we can import our code
# without a full Home Assistant installation.
for mod in [
    "homeassistant",
    "homeassistant.config_entries",
    "homeassistant.const",
    "homeassistant.core",
    "voluptuous",
]:
    sys.modules.setdefault(mod, MagicMock())

import pytest
from aioresponses import aioresponses


@pytest.fixture
def mock_aioresponse():
    """Provide a mocked aiohttp responses context."""
    with aioresponses() as m:
        yield m


@pytest.fixture
def mock_device_host() -> str:
    """Return a test device host."""
    return "192.168.1.100"


@pytest.fixture
def mock_device_port() -> int:
    """Return a test device port."""
    return 8080


@pytest.fixture
def mock_base_url(mock_device_host: str, mock_device_port: int) -> str:
    """Return the expected base URL for the test device."""
    return f"http://{mock_device_host}:{mock_device_port}"
