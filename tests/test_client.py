"""Tests for the Pool Lab TCP client."""

from __future__ import annotations

import asyncio

import pytest

from custom_components.pool_lab.client import PoolLabClient

SAMPLE_STATUS = (
    "FG1=1aea09ff;FG2=0;CHLORSTAT=0300;SYSSTAT=0;FILTER=1;SPAMODE=0;"
    "CHLORTARG=0;CHLORACT=0;PUMPSPEED=2;WATERTEMP=270"
)


class TestPoolLabClientInit:
    """Tests for client initialization."""

    def test_host_and_port_stored(self) -> None:
        """Test that host and port are accessible."""
        client = PoolLabClient("10.0.0.1", 9090)
        assert client.host == "10.0.0.1"
        assert client.port == 9090

    def test_not_connected_initially(self) -> None:
        """Test that a new client is not connected."""
        client = PoolLabClient("pool-lab.local", 8080)
        assert client.connected is False


class TestPoolLabClientConnect:
    """Tests for the connect method."""

    async def test_connect_success(self, tcp_server) -> None:
        """Test successful connection with handshake and initial status."""

        async def handler(reader, writer):
            writer.write(b"connected\n")
            await writer.drain()
            writer.write(f"{SAMPLE_STATUS}\n".encode())
            await writer.drain()
            await reader.read(1024)
            writer.close()

        host, port = await tcp_server(handler)
        client = PoolLabClient(host, port)

        await client.connect()
        assert client.connected is True
        assert client.initial_status == SAMPLE_STATUS
        await client.close()

    async def test_connect_wrong_handshake(self, tcp_server) -> None:
        """Test that an unexpected handshake raises ConnectionError."""

        async def handler(reader, writer):
            writer.write(b"unexpected_response\n")
            await writer.drain()
            writer.close()

        host, port = await tcp_server(handler)
        client = PoolLabClient(host, port)

        with pytest.raises(ConnectionError, match="Unexpected handshake"):
            await client.connect()

        assert client.connected is False

    async def test_connect_device_unreachable(self) -> None:
        """Test that a connection to a closed port raises ConnectionError."""
        client = PoolLabClient("127.0.0.1", 1)

        with pytest.raises(ConnectionError, match="Cannot connect"):
            await client.connect()

    async def test_connect_timeout(self, tcp_server, monkeypatch) -> None:
        """Test that a non-responsive device times out."""
        import custom_components.pool_lab.client as client_mod

        monkeypatch.setattr(client_mod, "DEFAULT_TIMEOUT", 0.1)

        async def handler(reader, writer):
            await asyncio.sleep(10)
            writer.close()

        host, port = await tcp_server(handler)
        client = PoolLabClient(host, port)

        with pytest.raises((ConnectionError, asyncio.TimeoutError)):
            await client.connect()


class TestPoolLabClientClose:
    """Tests for the close method."""

    async def test_close_without_connect(self) -> None:
        """Test that closing a never-connected client is safe."""
        client = PoolLabClient("127.0.0.1", 8080)
        await client.close()

    async def test_close_after_connect(self, tcp_server) -> None:
        """Test that close properly tears down the connection."""

        async def handler(reader, writer):
            writer.write(b"connected\n")
            await writer.drain()
            writer.write(f"{SAMPLE_STATUS}\n".encode())
            await writer.drain()
            await reader.read(1024)
            writer.close()

        host, port = await tcp_server(handler)
        client = PoolLabClient(host, port)

        await client.connect()
        assert client.connected is True

        await client.close()
        assert client.connected is False


class TestPoolLabClientSendCommand:
    """Tests for sending commands through the client."""

    async def test_send_without_connect_raises(self) -> None:
        """Test that send_command fails if client is not connected."""
        client = PoolLabClient("127.0.0.1", 8080)

        with pytest.raises(ConnectionError, match="not connected"):
            await client.send_command("up;\r")

    async def test_send_command_and_receive_response(self, tcp_server) -> None:
        """Test sending a command and receiving a status update response."""

        async def handler(reader, writer):
            # Handshake
            writer.write(b"connected\n")
            await writer.drain()
            writer.write(f"{SAMPLE_STATUS}\n".encode())
            await writer.drain()
            # Wait for any data from client (command)
            await reader.read(100)
            # Respond with status update
            writer.write(b"FILTER=1;SPAMODE=0;WATERTEMP=280\n")
            await writer.drain()
            # Wait for client to read before closing
            await asyncio.sleep(0.1)
            writer.close()
            await writer.wait_closed()

        host, port = await tcp_server(handler)
        client = PoolLabClient(host, port)

        await client.connect()
        response = await client.send_command("up;\r")
        assert "FILTER=1" in response
        assert "WATERTEMP=280" in response
        await client.close()
