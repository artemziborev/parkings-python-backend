"""Use cases - application layer orchestration."""

from parking.domain.interfaces import ParkingDataSource, ParkingStorage
from parking.domain.models import Coordinates, Parking
from parking.domain.services import ParkingSearchService, ParkingSynchronizationService


class UseCases:
    """Main application use cases - orchestrates domain services."""

    def __init__(
        self,
        storage: ParkingStorage,
        data_source: ParkingDataSource,
    ) -> None:
        self._storage = storage
        self._data_source = data_source

        # Initialize domain services
        self._synchronization_service = ParkingSynchronizationService(
            storage, data_source
        )
        self._search_service = ParkingSearchService(storage)

    async def save_or_update_parking_spots(self) -> None:
        """Synchronizes parking data from external source."""
        await self._synchronization_service.synchronize_parking_data()

    async def get_parking_spot_by_coordinates(
        self,
        coordinates: Coordinates,
        distance: int,
        limit: int,
    ) -> list[Parking]:
        """Finds parkings by coordinates within given radius."""
        return await self._search_service.search_by_coordinates(
            coordinates, distance, limit
        )

    async def get_parking_by_id(self, parking_id: int) -> Parking | None:
        """Gets parking by ID."""
        return await self._search_service.search_by_id(parking_id)

    async def get_parking_by_name(
        self,
        name: str,
        limit: int,
    ) -> list[Parking]:
        """Finds parkings by name."""
        return await self._search_service.search_by_name(name, limit)

    async def search_parking_by_name_and_number(
        self,
        name: str | None,
        number: str | None,
        limit: int,
    ) -> list[Parking]:
        """Finds parkings by name and/or number."""
        return await self._search_service.search_by_name_and_number(name, number, limit)

    async def search_parking_by_address(
        self, address_query: str, limit: int
    ) -> list[Parking]:
        """Finds parkings by address."""
        return await self._search_service.search_by_address(address_query, limit)

    async def get_all_parkings(self, limit: int | None = None) -> list[Parking]:
        """Gets all parkings with optional limit."""
        return await self._search_service.get_all_parkings(limit)
