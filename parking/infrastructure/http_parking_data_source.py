"""HTTP client for fetching parking data."""

from typing import Any

import httpx
import structlog

from parking.application.config import ParkingDataSourceConfig
from parking.domain.interfaces import ParkingDataSource
from parking.domain.models import Parking

logger = structlog.get_logger()


class HttpParkingDataSource(ParkingDataSource):
    """HTTP client for loading parking data from external API."""

    def __init__(self, config: ParkingDataSourceConfig) -> None:
        self._config = config
        self._client = httpx.AsyncClient(timeout=config.timeout_secs)

    async def _make_http_request(self) -> httpx.Response:
        """Makes HTTP request to fetch parking data."""
        logger.info("Fetching parking data", url=self._config.url)

        response = await self._client.get(self._config.url)
        response.raise_for_status()

        logger.info("Received response", status_code=response.status_code)
        return response

    def _parse_api_response(self, data: dict[str, Any]) -> list[dict[str, Any]]:
        """Parses API response and extracts raw parking data."""
        # API returns object with parkings field
        if isinstance(data, dict) and "parkings" in data:
            raw_parkings: list[dict[str, Any]] = data["parkings"]
            logger.info("Found parkings in response", total=data.get("total", 0))
        else:
            # Fallback for old format - data should be a list
            raw_parkings = data if isinstance(data, list) else []
            logger.info("Using direct array format")

        return raw_parkings

    def _parse_parkings_from_data(
        self, raw_parkings: list[dict[str, Any]]
    ) -> list[Parking]:
        """Parses raw parking data into Parking objects."""
        parkings = []
        for item in raw_parkings:
            try:
                parking = Parking.model_validate(item)
                parkings.append(parking)
            except Exception as e:
                logger.warning(
                    "Failed to parse parking",
                    parking_id=item.get("_id", "unknown"),
                    error=str(e),
                )
                continue

        logger.info("Parsed parkings", total=len(parkings))
        return parkings

    async def fetch_parking_data(self) -> list[Parking]:
        """Fetches parking data from external source."""
        try:
            # Make HTTP request
            response = await self._make_http_request()

            # Parse response data
            data = response.json()
            raw_parkings = self._parse_api_response(data)

            # Parse parkings from raw data
            parkings = self._parse_parkings_from_data(raw_parkings)

            return parkings

        except httpx.HTTPError as e:
            logger.error("HTTP error while fetching parking data", error=str(e))
            raise
        except Exception as e:
            logger.error("Unexpected error while fetching parking data", error=str(e))
            raise

    async def close(self) -> None:
        """Closes HTTP client."""
        await self._client.aclose()
        logger.info("HTTP client closed")
