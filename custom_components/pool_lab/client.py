"""TCP client for communicating with Pool Lab devices.

Pool Lab devices use a raw TCP socket protocol. Upon connection,
the device responds with 'connected' to confirm the link is established.
"""

from __future__ import annotations

import asyncio
import logging

_LOGGER = logging.getLogger(__name__)

DEFAULT_TIMEOUT = 10.0
CONNECT_RESPONSE = "connected"


class PoolLabClient:
    """TCP client for Pool Lab device communication."""

    def __init__(self, host: str, port: int) -> None:
        """Initialize the client."""
        self._host = host
        self._port = port
        self._reader: asyncio.StreamReader | None = None
        self._writer: asyncio.StreamWriter | None = None

    @property
    def host(self) -> str:
        """Return the device host."""
        return self._host

    @property
    def port(self) -> int:
        """Return the device port."""
        return self._port

    @property
    def connected(self) -> bool:
        """Return True if the client has an active connection."""
        return self._writer is not None and not self._writer.is_closing()

    async def connect(self) -> None:
        """Establish a TCP connection to the Pool Lab device.

        Opens a TCP socket and waits for the device to respond with
        'connected' to confirm the link is established.

        Raises:
            ConnectionError: If the device cannot be reached or does not
                respond with the expected handshake.
        """
        try:
            self._reader, self._writer = await asyncio.wait_for(
                asyncio.open_connection(self._host, self._port),
                timeout=DEFAULT_TIMEOUT,
            )
        except (TimeoutError, OSError) as err:
            raise ConnectionError(
                f"Cannot connect to Pool Lab device at {self._host}:{self._port}: {err}"
            ) from err

        # Wait for the device handshake response
        try:
            data = await asyncio.wait_for(
                self._reader.readline(),
                timeout=DEFAULT_TIMEOUT,
            )
            response = data.decode().strip()
        except (TimeoutError, OSError) as err:
            await self.close()
            raise ConnectionError(
                f"Pool Lab device at {self._host}:{self._port} did not respond: {err}"
            ) from err

        if response != CONNECT_RESPONSE:
            await self.close()
            raise ConnectionError(
                f"Unexpected handshake from Pool Lab device at "
                f"{self._host}:{self._port}: {response!r}"
            )

        _LOGGER.debug(
            "Successfully connected to Pool Lab device at %s:%s",
            self._host,
            self._port,
        )

    async def close(self) -> None:
        """Close the TCP connection."""
        if self._writer is not None:
            try:
                self._writer.close()
                await self._writer.wait_closed()
            except OSError:
                pass
            self._writer = None
            self._reader = None

    async def send(self, message: str) -> str:
        """Send a message to the device and read the response.

        Args:
            message: The command string to send to the device.

        Returns:
            The response string from the device.

        Raises:
            ConnectionError: If the client is not connected.
        """
        if not self.connected:
            raise ConnectionError("Client is not connected. Call connect() first.")

        try:
            self._writer.write(f"{message}\n".encode())
            await self._writer.drain()

            data = await asyncio.wait_for(
                self._reader.readline(),
                timeout=DEFAULT_TIMEOUT,
            )
            return data.decode().strip()
        except (TimeoutError, OSError) as err:
            await self.close()
            raise ConnectionError(f"Communication error with Pool Lab device: {err}") from err
