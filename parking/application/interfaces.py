"""Interfaces for the application layer."""

from abc import ABC, abstractmethod
from typing import List, Optional

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
    ) -> List[Parking]:
        """Finds parkings by coordinates within given radius."""
        pass
    
    @abstractmethod
    async def find_by_id(self, parking_id: int) -> Optional[Parking]:
        """Finds parking by ID."""
        pass
    
    @abstractmethod
    async def find_by_name(self, name: str, limit: int) -> List[Parking]:
        """Finds parkings by name."""
        pass
    
    @abstractmethod
    async def find_by_name_and_number(
        self,
        name: Optional[str],
        number: Optional[str],
        limit: int,
    ) -> List[Parking]:
        """Finds parkings by name and/or number."""
        pass
    
    @abstractmethod
    async def find_by_address(self, address_query: str, limit: int) -> List[Parking]:
        """Finds parkings by address."""
        pass
    
    @abstractmethod
    async def find_all(self, limit: Optional[int] = None) -> List[Parking]:
        """Gets all parkings with optional limit."""
        pass


class ParkingDataSource(ABC):
    """Interface for parking data source."""
    
    @abstractmethod
    async def fetch_parking_data(self) -> List[Parking]:
        """Fetches parking data from external source."""
        pass
