"""Tests for the Pool Lab HTTP client."""

from __future__ import annotations

import pytest
from aioresponses import aioresponses

from custom_components.pool_lab.client import PoolLabClient


class TestPoolLabClientInit:
    """Tests for client initialization."""

    def test_base_url_constructed_correctly(self) -> None:
        """Test that the base URL is built from host and port."""
        client = PoolLabClient("10.0.0.1", 9090)
        assert client.base_url == "http://10.0.0.1:9090"

    def test_default_port(self) -> None:
        """Test client with standard port."""
        client = PoolLabClient("pool-lab.local", 80)
        assert client.base_url == "http://pool-lab.local:80"


class TestPoolLabClientConnect:
    """Tests for the connect method."""

    async def test_connect_success(
        self, mock_device_host: str, mock_device_port: int, mock_base_url: str
    ) -> None:
        """Test successful connection to device."""
        client = PoolLabClient(mock_device_host, mock_device_port)

        with aioresponses() as m:
            m.get(f"{mock_base_url}/", status=200)
            await client.connect()

        # Session should be open after successful connect
        await client.close()

    async def test_connect_device_returns_error(
        self, mock_device_host: str, mock_device_port: int, mock_base_url: str
    ) -> None:
        """Test that a 500 response raises ConnectionError."""
        client = PoolLabClient(mock_device_host, mock_device_port)

        with aioresponses() as m:
            m.get(f"{mock_base_url}/", status=500)
            with pytest.raises(ConnectionError, match="HTTP 500"):
                await client.connect()

    async def test_connect_device_unreachable(
        self, mock_device_host: str, mock_device_port: int, mock_base_url: str
    ) -> None:
        """Test that a network error raises ConnectionError."""
        client = PoolLabClient(mock_device_host, mock_device_port)

        with aioresponses() as m:
            m.get(f"{mock_base_url}/", exception=OSError("Connection refused"))
            with pytest.raises(ConnectionError, match="Cannot connect"):
                await client.connect()


class TestPoolLabClientClose:
    """Tests for the close method."""

    async def test_close_without_connect(
        self, mock_device_host: str, mock_device_port: int
    ) -> None:
        """Test that closing a never-connected client is safe."""
        client = PoolLabClient(mock_device_host, mock_device_port)
        await client.close()  # Should not raise

    async def test_close_after_connect(
        self, mock_device_host: str, mock_device_port: int, mock_base_url: str
    ) -> None:
        """Test that close properly tears down the session."""
        client = PoolLabClient(mock_device_host, mock_device_port)

        with aioresponses() as m:
            m.get(f"{mock_base_url}/", status=200)
            await client.connect()

        await client.close()


class TestPoolLabClientRequest:
    """Tests for making requests through the client."""

    async def test_request_without_connect_raises(
        self, mock_device_host: str, mock_device_port: int
    ) -> None:
        """Test that requests fail if client is not connected."""
        client = PoolLabClient(mock_device_host, mock_device_port)

        with pytest.raises(ConnectionError, match="not connected"):
            await client.get("/api/status")
