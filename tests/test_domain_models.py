"""Tests for domain models."""

from parking.domain.models import (
    ActiveParkings,
    Address,
    Category,
    Coordinates,
    Geometry,
    LangString,
    Parking,
    Spaces,
    filter_active_parkings,
)


def test_coordinates_creation():
    """Tests coordinates creation."""
    coords = Coordinates(latitude=55.7558, longitude=37.6176)
    assert coords.latitude == 55.7558
    assert coords.longitude == 37.6176


def test_parking_is_active():
    """Tests parking activity check."""
    # Active parking
    active_parking = Parking(
        _id=1,
        address=Address(
            house=LangString(en="1", ru="1"),
            street=LangString(en="Test St", ru="Test St"),
        ),
        blocked=False,
        category=Category(_id=1),
        center=Geometry(type="Point", coordinates=(37.6176, 55.7558)),
        city="Moscow",
        contacts=LangString(en="", ru=""),
        description=LangString(en="", ru=""),
        location=Geometry(type="Point", coordinates=(37.6176, 55.7558)),
        name=LangString(en="Active Parking", ru="Active Parking"),
        resolutionAddress="Test address",
        spaces=Spaces(total=10),
    )

    assert active_parking.is_active() is True

    # Disabled parking
    disabled_parking = Parking(
        _id=2,
        address=Address(
            house=LangString(en="2", ru="2"),
            street=LangString(en="Test St", ru="Test St"),
        ),
        blocked=False,
        category=Category(_id=1),
        center=Geometry(type="Point", coordinates=(37.6176, 55.7558)),
        city="Moscow",
        contacts=LangString(en="", ru=""),
        description=LangString(en="", ru=""),
        location=Geometry(type="Point", coordinates=(37.6176, 55.7558)),
        name=LangString(en="Disabled Parking", ru="Disabled Parking"),
        resolutionAddress="Test address",
        spaces=Spaces(total=10),
    )

    assert disabled_parking.is_active() is False


def test_filter_active_parkings():
    """Tests active parkings filtering."""
    parkings = [
        Parking(
            _id=i,
            address=Address(
                house=LangString(en=str(i), ru=str(i)),
                street=LangString(en="Test St", ru="Test St"),
            ),
            blocked=False,
            category=Category(_id=1),
            center=Geometry(type="Point", coordinates=(37.6176, 55.7558)),
            city="Moscow",
            contacts=LangString(en="", ru=""),
            description=LangString(en="", ru=""),
            location=Geometry(type="Point", coordinates=(37.6176, 55.7558)),
            name=LangString(
                en=name,
                ru=name,
            ),
            resolutionAddress="Test address",
            spaces=Spaces(total=10),
        )
        for i, name in enumerate(
            [
                "Active Parking 1",
                "Disabled Parking",
                "Active Parking 2",
            ],
            1,
        )
    ]

    active_parkings = filter_active_parkings(parkings)

    assert len(active_parkings) == 2
    assert not active_parkings.is_empty()

    active_list = active_parkings.to_list()
    assert len(active_list) == 2
    assert active_list[0].name.en == "Active Parking 1"
    assert active_list[1].name.en == "Active Parking 2"


def test_active_parkings_empty():
    """Tests empty active parkings collection."""
    empty_parkings = ActiveParkings([])

    assert len(empty_parkings) == 0
    assert empty_parkings.is_empty() is True
    assert empty_parkings.to_list() == []
