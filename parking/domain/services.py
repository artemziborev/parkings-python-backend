"""Domain services for business logic."""

from typing import TYPE_CHECKING

import structlog

from parking.domain.models import Coordinates, Parking, filter_active_parkings

if TYPE_CHECKING:
    from parking.domain.interfaces import ParkingDataSource, ParkingStorage

logger = structlog.get_logger()


class ParkingSynchronizationService:
    """Service for parking data synchronization business logic."""

    def __init__(
        self, storage: "ParkingStorage", data_source: "ParkingDataSource"
    ) -> None:
        self._storage = storage
        self._data_source = data_source

    async def synchronize_parking_data(self) -> None:
        """Synchronizes parking data from external source."""
        logger.info("Starting parking data synchronization")

        # Get data from external source
        raw_parkings = await self._data_source.fetch_parking_data()
        total_count = len(raw_parkings)
        logger.info("Downloaded parking records", total_count=total_count)

        # Filter only active parkings
        processed_parkings = filter_active_parkings(raw_parkings)
        filtered_count = len(processed_parkings)
        disabled_count = total_count - filtered_count

        logger.info("Processed active parking records", filtered_count=filtered_count)
        logger.info(
            "Filtered out disabled parking records", disabled_count=disabled_count
        )

        # Save to storage
        await self._storage.upsert(processed_parkings)

        logger.info("Parking data synchronization completed successfully")


class ParkingSearchService:
    """Service for parking search business logic."""

    def __init__(self, storage: "ParkingStorage") -> None:
        self._storage = storage

    async def search_by_coordinates(
        self,
        coordinates: Coordinates,
        distance: int,
        limit: int,
    ) -> list[Parking]:
        """Finds parkings by coordinates within given radius."""
        parkings = await self._storage.find_by_coordinates(coordinates, distance, limit)
        return parkings

    async def search_by_id(self, parking_id: int) -> Parking | None:
        """Gets parking by ID."""
        parking = await self._storage.find_by_id(parking_id)
        return parking

    async def search_by_name(
        self,
        name: str,
        limit: int,
    ) -> list[Parking]:
        """Finds parkings by name."""
        parkings = await self._storage.find_by_name(name, limit)
        return parkings

    async def search_by_name_and_number(
        self,
        name: str | None,
        number: str | None,
        limit: int,
    ) -> list[Parking]:
        """Finds parkings by name and/or number."""
        parkings = await self._storage.find_by_name_and_number(name, number, limit)
        return parkings

    async def search_by_address(self, address_query: str, limit: int) -> list[Parking]:
        """Finds parkings by address."""
        parkings = await self._storage.find_by_address(address_query, limit)
        return parkings

    async def get_all_parkings(self, limit: int | None = None) -> list[Parking]:
        """Gets all parkings with optional limit."""
        parkings = await self._storage.find_all(limit)
        return parkings
