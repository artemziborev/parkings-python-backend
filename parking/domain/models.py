"""Domain models."""

from __future__ import annotations

from enum import Enum
from typing import Any, Iterator, List, Optional, Tuple, Union

from pydantic import BaseModel, Field


class Coordinates(BaseModel):
    """Geographic coordinates."""
    
    latitude: float = Field(..., description="Latitude")
    longitude: float = Field(..., description="Longitude")


class Geometry(BaseModel):
    """Object geometry (GeoJSON)."""
    
    type: str = Field(..., description="Geometry type")
    coordinates: Union[
        Tuple[float, float],  # Point
        List[Tuple[float, float]],  # LineString
        List[List[Tuple[float, float]]]  # Polygon
    ] = Field(..., description="Coordinates")


class LangString(BaseModel):
    """String in two languages."""
    
    en: str = Field(..., description="English")
    ru: str = Field(..., description="Russian")


class Address(BaseModel):
    """Parking address."""
    
    house: LangString = Field(..., description="House")
    street: LangString = Field(..., description="Street")


class Spaces(BaseModel):
    """Information about parking spaces."""
    
    common: Optional[int] = Field(None, description="Common spaces")
    total: Optional[int] = Field(None, description="Total spaces")


class Price(BaseModel):
    """Price range."""
    
    max: int = Field(..., description="Maximum price")
    min: int = Field(..., description="Minimum price")


class ZonePrice(BaseModel):
    """Price in zone for vehicle type."""
    
    price: Optional[Price] = Field(None, description="Price range")
    vehicle_type: str = Field(..., alias="vehicleType", description="Vehicle type")


class Category(BaseModel):
    """Parking category."""
    
    id: int = Field(..., alias="_id", description="Category ID")
    icon_name: Optional[str] = Field(None, alias="iconName", description="Icon name")
    zone_purpose: Optional[str] = Field(
        None, alias="zonePurpose", description="Zone purpose"
    )


class Zone(BaseModel):
    """Parking zone."""
    
    id: int = Field(..., alias="_id", description="Zone ID")
    active: bool = Field(..., description="Active zone")
    city: str = Field(..., description="City")
    description: LangString = Field(..., description="Description")
    number: str = Field(..., description="Zone number")
    prices: Optional[List[ZonePrice]] = Field(None, description="Prices")
    zone_type: str = Field(..., alias="type", description="Zone type")


class Parking(BaseModel):
    """Parking."""
    
    id: int = Field(..., alias="_id", description="Parking ID")
    address: Address = Field(..., description="Address")
    blocked: bool = Field(..., description="Blocked")
    category: Category = Field(..., description="Category")
    center: Geometry = Field(..., description="Parking center")
    city: str = Field(..., description="City")
    contacts: LangString = Field(..., description="Contacts")
    custom_type: Optional[LangString] = Field(
        None, alias="customType", description="Custom type"
    )
    description: LangString = Field(..., description="Description")
    location: Geometry = Field(..., description="Location")
    name: LangString = Field(..., description="Name")
    litera: Optional[str] = Field(None, description="Litera")
    resolution_address: str = Field(
        ..., alias="resolutionAddress", description="Resolution address"
    )
    spaces: Spaces = Field(..., description="Spaces")
    subway: Optional[LangString] = Field(None, description="Metro station")
    zone: Optional[Zone] = Field(None, description="Zone")
    distance: Optional[float] = Field(None, description="Distance in meters")
    
    def is_active(self) -> bool:
        """Checks if the parking is active (not disabled)."""
        return "disabled parking" not in self.name.en.lower()


class ActiveParkings:
    """Collection of active parkings."""
    
    def __init__(self, parkings: List[Parking]) -> None:
        self._parkings = parkings
    
    def __len__(self) -> int:
        return len(self._parkings)
    
    def __iter__(self) -> Iterator[Parking]:
        return iter(self._parkings)
    
    def is_empty(self) -> bool:
        """Checks if the collection is empty."""
        return len(self._parkings) == 0
    
    def to_list(self) -> List[Parking]:
        """Returns list of parkings."""
        return self._parkings.copy()


def filter_active_parkings(parkings: List[Parking]) -> ActiveParkings:
    """Filters only active parkings."""
    active_parkings = [parking for parking in parkings if parking.is_active()]
    return ActiveParkings(active_parkings)
