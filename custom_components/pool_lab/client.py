"""TCP client for communicating with Pool Lab devices.

Pool Lab devices use a raw TCP socket protocol. Upon connection,
the device responds with 'connected' followed by a full status update.
Commands are sent as text terminated with CR, and the device responds
with a new status update after each command.
"""

from __future__ import annotations

import asyncio
import logging

_LOGGER = logging.getLogger(__name__)

DEFAULT_TIMEOUT = 10.0
CONNECT_RESPONSE = "connected"


class PoolLabClient:
    """Low-level TCP client for Pool Lab device communication.

    Handles connection lifecycle and raw message exchange.
    Does not interpret the content of messages — that's the
    protocol layer's responsibility.
    """

    def __init__(self, host: str, port: int) -> None:
        """Initialize the client."""
        self._host = host
        self._port = port
        self._reader: asyncio.StreamReader | None = None
        self._writer: asyncio.StreamWriter | None = None
        self._lock = asyncio.Lock()
        self._initial_status: str | None = None

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

    @property
    def initial_status(self) -> str | None:
        """Return the initial status received during handshake.

        This is the full status update the device sends immediately
        after the 'connected' response. Available only once after connect.
        """
        return self._initial_status

    async def connect(self) -> None:
        """Establish a TCP connection to the Pool Lab device.

        Opens a TCP socket, waits for the 'connected' handshake,
        then reads the initial status update that follows.

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

        # Read the handshake line
        handshake = await self._read_line()
        if handshake != CONNECT_RESPONSE:
            await self.close()
            raise ConnectionError(
                f"Unexpected handshake from Pool Lab device at "
                f"{self._host}:{self._port}: {handshake!r}"
            )

        # Read the initial status update that follows the handshake
        self._initial_status = await self._read_line()

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

    async def send_command(self, command: str) -> str:
        """Send a command and read the response.

        Commands are sent as-is (caller must include terminators).
        The device responds with a full status update string.

        Args:
            command: The complete command string (e.g. "up;\\r").

        Returns:
            The raw status update response from the device.

        Raises:
            ConnectionError: If the client is not connected or
                communication fails.
        """
        if not self.connected:
            raise ConnectionError("Client is not connected. Call connect() first.")

        async with self._lock:
            try:
                self._writer.write(command.encode())
                await self._writer.drain()
                return await self._read_line()
            except (TimeoutError, OSError) as err:
                await self.close()
                raise ConnectionError(f"Communication error with Pool Lab device: {err}") from err

    async def _read_line(self) -> str:
        """Read a single line from the device with timeout.

        Returns:
            The decoded and stripped response line.

        Raises:
            ConnectionError: If reading times out or fails.
        """
        try:
            data = await asyncio.wait_for(
                self._reader.readline(),
                timeout=DEFAULT_TIMEOUT,
            )
            if not data:
                raise ConnectionError("Device closed the connection")
            return data.decode().strip()
        except (TimeoutError, OSError) as err:
            await self.close()
            raise ConnectionError(
                f"Pool Lab device at {self._host}:{self._port} did not respond: {err}"
            ) from err
