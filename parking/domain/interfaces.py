"""Domain interfaces - contracts for business logic."""

from abc import ABC, abstractmethod

from parking.domain.models import ActiveParkings, Coordinates, Parking


class ParkingStorage(ABC):
    """Interface for parking storage."""

    @abstractmethod
    async def upsert(self, active_parkings: ActiveParkings) -> None:
        """Saves or updates active parkings."""
        pass

    @abstractmethod
    async def find_by_coordinates(
        self,
        coords: Coordinates,
        distance: int,
        limit: int,
    ) -> list[Parking]:
        """Finds parkings by coordinates within given radius."""
        pass

    @abstractmethod
    async def find_by_id(self, parking_id: int) -> Parking | None:
        """Finds parking by ID."""
        pass

    @abstractmethod
    async def find_by_name(self, name: str, limit: int) -> list[Parking]:
        """Finds parkings by name."""
        pass

    @abstractmethod
    async def find_by_name_and_number(
        self,
        name: str | None,
        number: str | None,
        limit: int,
    ) -> list[Parking]:
        """Finds parkings by name and/or number."""
        pass

    @abstractmethod
    async def find_by_address(self, address_query: str, limit: int) -> list[Parking]:
        """Finds parkings by address."""
        pass

    @abstractmethod
    async def find_all(self, limit: int | None = None) -> list[Parking]:
        """Gets all parkings with optional limit."""
        pass


class ParkingDataSource(ABC):
    """Interface for parking data source."""

    @abstractmethod
    async def fetch_parking_data(self) -> list[Parking]:
        """Fetches parking data from external source."""
        pass
