"""Domain models."""

from __future__ import annotations

from typing import TYPE_CHECKING

from pydantic import BaseModel, Field

if TYPE_CHECKING:
    from collections.abc import Iterator


class Coordinates(BaseModel):
    """Geographic coordinates."""

    latitude: float = Field(..., description="Latitude")
    longitude: float = Field(..., description="Longitude")


class Geometry(BaseModel):
    """Object geometry (GeoJSON)."""

    type: str = Field(..., description="Geometry type")
    coordinates: (
        tuple[float, float]
        | list[tuple[float, float]]
        | list[list[tuple[float, float]]]
    ) = Field(..., description="Coordinates")


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

    common: int | None = Field(None, description="Common spaces")
    total: int | None = Field(None, description="Total spaces")


class Price(BaseModel):
    """Price range."""

    max: int = Field(..., description="Maximum price")
    min: int = Field(..., description="Minimum price")


class ZonePrice(BaseModel):
    """Price in zone for vehicle type."""

    price: Price | None = Field(None, description="Price range")
    vehicle_type: str = Field(..., alias="vehicleType", description="Vehicle type")


class Category(BaseModel):
    """Parking category."""

    id: int = Field(..., alias="_id", description="Category ID")
    icon_name: str | None = Field(None, alias="iconName", description="Icon name")
    zone_purpose: str | None = Field(
        None, alias="zonePurpose", description="Zone purpose"
    )


class Zone(BaseModel):
    """Parking zone."""

    id: int = Field(..., alias="_id", description="Zone ID")
    active: bool = Field(..., description="Active zone")
    city: str = Field(..., description="City")
    description: LangString = Field(..., description="Description")
    number: str = Field(..., description="Zone number")
    prices: list[ZonePrice] | None = Field(None, description="Prices")
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
    custom_type: LangString | None = Field(
        None, alias="customType", description="Custom type"
    )
    description: LangString = Field(..., description="Description")
    location: Geometry = Field(..., description="Location")
    name: LangString = Field(..., description="Name")
    litera: str | None = Field(None, description="Litera")
    resolution_address: str = Field(
        ..., alias="resolutionAddress", description="Resolution address"
    )
    spaces: Spaces = Field(..., description="Spaces")
    subway: LangString | None = Field(None, description="Metro station")
    zone: Zone | None = Field(None, description="Zone")
    distance: float | None = Field(None, description="Distance in meters")

    def is_active(self) -> bool:
        """Checks if the parking is active (not disabled)."""
        return "disabled parking" not in self.name.en.lower()


class ActiveParkings:
    """Collection of active parkings."""

    def __init__(self, parkings: list[Parking]) -> None:
        self._parkings = parkings

    def __len__(self) -> int:
        return len(self._parkings)

    def __iter__(self) -> Iterator[Parking]:
        return iter(self._parkings)

    def is_empty(self) -> bool:
        """Checks if the collection is empty."""
        return len(self._parkings) == 0

    def to_list(self) -> list[Parking]:
        """Returns list of parkings."""
        return self._parkings.copy()


def filter_active_parkings(parkings: list[Parking]) -> ActiveParkings:
    """Filters only active parkings."""
    active_parkings = [parking for parking in parkings if parking.is_active()]
    return ActiveParkings(active_parkings)
