"""Tests for the Pool Lab TCP client."""

from __future__ import annotations

import asyncio

import pytest

from custom_components.pool_lab.client import PoolLabClient


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
        """Test successful connection with handshake."""

        async def handler(reader, writer):
            writer.write(b"connected\n")
            await writer.drain()
            # Keep connection open until client disconnects
            await reader.read(1024)
            writer.close()

        host, port = await tcp_server(handler)
        client = PoolLabClient(host, port)

        await client.connect()
        assert client.connected is True
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
        client = PoolLabClient("127.0.0.1", 1)  # Port 1 should be refused

        with pytest.raises(ConnectionError, match="Cannot connect"):
            await client.connect()

    async def test_connect_timeout(self, tcp_server, monkeypatch) -> None:
        """Test that a non-responsive device times out."""
        import custom_components.pool_lab.client as client_mod

        monkeypatch.setattr(client_mod, "DEFAULT_TIMEOUT", 0.1)

        async def handler(reader, writer):
            # Never send the handshake
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
        await client.close()  # Should not raise

    async def test_close_after_connect(self, tcp_server) -> None:
        """Test that close properly tears down the connection."""

        async def handler(reader, writer):
            writer.write(b"connected\n")
            await writer.drain()
            await reader.read(1024)
            writer.close()

        host, port = await tcp_server(handler)
        client = PoolLabClient(host, port)

        await client.connect()
        assert client.connected is True

        await client.close()
        assert client.connected is False


class TestPoolLabClientSend:
    """Tests for sending messages through the client."""

    async def test_send_without_connect_raises(self) -> None:
        """Test that send fails if client is not connected."""
        client = PoolLabClient("127.0.0.1", 8080)

        with pytest.raises(ConnectionError, match="not connected"):
            await client.send("some_command")

    async def test_send_and_receive(self, tcp_server) -> None:
        """Test sending a command and receiving a response."""

        async def handler(reader, writer):
            writer.write(b"connected\n")
            await writer.drain()
            # Echo back whatever is received
            data = await reader.readline()
            writer.write(data)
            await writer.drain()
            await reader.read(1024)
            writer.close()

        host, port = await tcp_server(handler)
        client = PoolLabClient(host, port)

        await client.connect()
        response = await client.send("hello")
        assert response == "hello"
        await client.close()
