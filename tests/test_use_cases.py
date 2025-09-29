"""Tests for use cases."""

import pytest
from unittest.mock import AsyncMock

from parking.application.use_cases import UseCases
from parking.domain.models import (
    Coordinates, 
    Parking, 
    ActiveParkings,
    LangString,
    Address,
    Geometry,
    Category,
    Spaces,
    Zone
)


@pytest.fixture
def mock_storage():
    """Mock storage."""
    return AsyncMock()


@pytest.fixture
def mock_data_source():
    """Mock data source."""
    return AsyncMock()


@pytest.fixture
def use_cases(mock_storage, mock_data_source):
    """Creates use cases with mocks."""
    return UseCases(mock_storage, mock_data_source)


@pytest.fixture
def sample_parking():
    """Creates sample parking for tests."""
    return Parking(
        _id=1,
        address=Address(
            house=LangString(en="1", ru="1"),
            street=LangString(en="Test St", ru="Test St"),
        ),
        blocked=False,
        category=Category(_id=1, iconName="paid"),
        center=Geometry(type="Point", coordinates=[37.6176, 55.7558]),
        city="Moscow",
        contacts=LangString(en="Contact", ru="Contact"),
        description=LangString(en="Test parking", ru="Test parking"),
        location=Geometry(type="Point", coordinates=[37.6176, 55.7558]),
        name=LangString(en="Test Parking", ru="Test Parking"),
        resolutionAddress="Test address",
        spaces=Spaces(total=10, common=5),
        zone=Zone(
            _id=1,
            active=True,
            city="Moscow",
            description=LangString(en="Test zone", ru="Test zone"),
            number="A001",
            type="paid"
        )
    )


@pytest.mark.asyncio
async def test_save_or_update_parking_spots(use_cases, mock_storage, mock_data_source, sample_parking):
    """Tests parking synchronization."""
    # Setup
    mock_data_source.fetch_parking_data.return_value = [sample_parking]
    
    # Execute
    await use_cases.save_or_update_parking_spots()
    
    # Verify
    mock_data_source.fetch_parking_data.assert_called_once()
    mock_storage.upsert.assert_called_once()
    
    # Verify that ActiveParkings is passed
    call_args = mock_storage.upsert.call_args[0][0]
    assert isinstance(call_args, ActiveParkings)


@pytest.mark.asyncio
async def test_get_parking_spot_by_coordinates(use_cases, mock_storage, sample_parking):
    """Tests parking search by coordinates."""
    # Setup
    coordinates = Coordinates(latitude=55.7558, longitude=37.6176)
    mock_storage.find_by_coordinates.return_value = [sample_parking]
    
    # Execute
    result = await use_cases.get_parking_spot_by_coordinates(coordinates, 1000, 5)
    
    # Verify
    assert len(result) == 1
    assert result[0] == sample_parking
    mock_storage.find_by_coordinates.assert_called_once_with(coordinates, 1000, 5)


@pytest.mark.asyncio
async def test_get_parking_by_id(use_cases, mock_storage, sample_parking):
    """Tests parking retrieval by ID."""
    # Setup
    mock_storage.find_by_id.return_value = sample_parking
    
    # Execute
    result = await use_cases.get_parking_by_id(1)
    
    # Verify
    assert result == sample_parking
    mock_storage.find_by_id.assert_called_once_with(1)


@pytest.mark.asyncio
async def test_get_parking_by_id_not_found(use_cases, mock_storage):
    """Tests retrieval of non-existent parking."""
    # Setup
    mock_storage.find_by_id.return_value = None
    
    # Execute
    result = await use_cases.get_parking_by_id(999)
    
    # Verify
    assert result is None
    mock_storage.find_by_id.assert_called_once_with(999)


@pytest.mark.asyncio
async def test_get_parking_by_name(use_cases, mock_storage, sample_parking):
    """Tests parking search by name."""
    # Setup
    mock_storage.find_by_name.return_value = [sample_parking]
    
    # Execute
    result = await use_cases.get_parking_by_name("Test", 10)
    
    # Verify
    assert len(result) == 1
    assert result[0] == sample_parking
    mock_storage.find_by_name.assert_called_once_with("Test", 10)


@pytest.mark.asyncio
async def test_search_parking_by_name_and_number(use_cases, mock_storage, sample_parking):
    """Tests parking search by name and number."""
    # Setup
    mock_storage.find_by_name_and_number.return_value = [sample_parking]
    
    # Execute
    result = await use_cases.search_parking_by_name_and_number("Test", "A001", 10)
    
    # Verify
    assert len(result) == 1
    assert result[0] == sample_parking
    mock_storage.find_by_name_and_number.assert_called_once_with("Test", "A001", 10)


@pytest.mark.asyncio
async def test_search_parking_by_address(use_cases, mock_storage, sample_parking):
    """Tests parking search by address."""
    # Setup
    mock_storage.find_by_address.return_value = [sample_parking]
    
    # Execute
    result = await use_cases.search_parking_by_address("Test St", 10)
    
    # Verify
    assert len(result) == 1
    assert result[0] == sample_parking
    mock_storage.find_by_address.assert_called_once_with("Test St", 10)


@pytest.mark.asyncio
async def test_get_all_parkings(use_cases, mock_storage, sample_parking):
    """Tests retrieval of all parkings."""
    # Setup
    mock_storage.find_all.return_value = [sample_parking]
    
    # Execute
    result = await use_cases.get_all_parkings(limit=100)
    
    # Verify
    assert len(result) == 1
    assert result[0] == sample_parking
    mock_storage.find_all.assert_called_once_with(100)


@pytest.mark.asyncio
async def test_get_all_parkings_no_limit(use_cases, mock_storage, sample_parking):
    """Tests retrieval of all parkings without restrictions."""
    # Setup
    mock_storage.find_all.return_value = [sample_parking]
    
    # Execute
    result = await use_cases.get_all_parkings()
    
    # Verify
    assert len(result) == 1
    assert result[0] == sample_parking
    mock_storage.find_all.assert_called_once_with(None)

