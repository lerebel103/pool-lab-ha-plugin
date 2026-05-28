"""HTTP client for communicating with Pool Lab devices."""

from __future__ import annotations

import logging

import aiohttp

_LOGGER = logging.getLogger(__name__)

DEFAULT_TIMEOUT = aiohttp.ClientTimeout(total=10)


class PoolLabClient:
    """HTTP client for Pool Lab device communication."""

    def __init__(self, host: str, port: int) -> None:
        """Initialize the client."""
        self._host = host
        self._port = port
        self._base_url = f"http://{host}:{port}"
        self._session: aiohttp.ClientSession | None = None

    @property
    def base_url(self) -> str:
        """Return the base URL of the device."""
        return self._base_url

    async def connect(self) -> None:
        """Establish a connection to the Pool Lab device.

        Creates an aiohttp session and verifies the device is reachable.
        Raises an exception if the device cannot be reached.
        """
        self._session = aiohttp.ClientSession(
            base_url=self._base_url,
            timeout=DEFAULT_TIMEOUT,
        )

        # Verify the device is reachable with a simple GET request
        try:
            async with self._session.get("/") as response:
                if response.status >= 400:
                    raise ConnectionError(f"Pool Lab device returned HTTP {response.status}")
                _LOGGER.debug("Successfully connected to Pool Lab device at %s", self._base_url)
        except (aiohttp.ClientError, OSError) as err:
            await self.close()
            raise ConnectionError(
                f"Cannot connect to Pool Lab device at {self._base_url}: {err}"
            ) from err

    async def close(self) -> None:
        """Close the HTTP session."""
        if self._session and not self._session.closed:
            await self._session.close()
            self._session = None

    async def request(self, method: str, path: str, **kwargs) -> aiohttp.ClientResponse:
        """Make an HTTP request to the device.

        Args:
            method: HTTP method (GET, POST, etc.)
            path: URL path relative to the base URL.
            **kwargs: Additional arguments passed to aiohttp request.

        Returns:
            The aiohttp response object.

        Raises:
            ConnectionError: If the session is not established.
        """
        if self._session is None or self._session.closed:
            raise ConnectionError("Client is not connected. Call connect() first.")

        async with self._session.request(method, path, **kwargs) as response:
            # Read the response body so it's available after context exit
            await response.read()
            return response

    async def get(self, path: str, **kwargs) -> aiohttp.ClientResponse:
        """Make a GET request."""
        return await self.request("GET", path, **kwargs)

    async def post(self, path: str, **kwargs) -> aiohttp.ClientResponse:
        """Make a POST request."""
        return await self.request("POST", path, **kwargs)
