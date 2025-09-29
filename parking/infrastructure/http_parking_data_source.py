"""HTTP client for fetching parking data."""

from typing import List

import httpx
import structlog

from parking.application.interfaces import ParkingDataSource
from parking.domain.models import Parking
from parking.infrastructure.config import ParkingDataSourceConfig


logger = structlog.get_logger()


class HttpParkingDataSource(ParkingDataSource):
    """HTTP client for loading parking data from external API."""
    
    def __init__(self, config: ParkingDataSourceConfig) -> None:
        self._config = config
        self._client = httpx.AsyncClient(timeout=config.timeout_secs)
    
    async def fetch_parking_data(self) -> List[Parking]:
        """Fetches parking data from external source."""
        logger.info("Fetching parking data", url=self._config.url)
        
        try:
            response = await self._client.get(self._config.url)
            response.raise_for_status()
            
            data = response.json()
            logger.info("Received response", status_code=response.status_code)
            
            # API returns object with parkings field
            if isinstance(data, dict) and "parkings" in data:
                raw_parkings = data["parkings"]
                logger.info("Found parkings in response", total=data.get("total", 0))
            else:
                # Fallback for old format
                raw_parkings = data
                logger.info("Using direct array format")
            
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
