"""Tests for HTTP server."""

from unittest.mock import AsyncMock

import pytest
from fastapi import FastAPI
from fastapi.testclient import TestClient

from parking.api.http_server import setup_routes
from parking.application.use_cases import UseCases
from parking.domain.models import (
    Address,
    Category,
    Geometry,
    LangString,
    Parking,
    Spaces,
    Zone,
)


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
            type="paid",
        ),
    )


@pytest.fixture
def mock_use_cases():
    """Mock use cases."""
    return AsyncMock(spec=UseCases)


@pytest.fixture
def test_app(mock_use_cases):
    """Creates test FastAPI application."""
    app = FastAPI()

    # Mock application state
    app.state.use_cases = mock_use_cases

    setup_routes(app)
    return app


@pytest.fixture
def client(test_app):
    """Creates test client."""
    return TestClient(test_app)


def test_health_check(client):
    """Tests health check endpoint."""
    response = client.get("/health")
    assert response.status_code == 200
    assert response.json() == {"status": "healthy"}


def test_search_parkings_by_coords_success(client, mock_use_cases, sample_parking):
    """Tests successful parking search by coordinates."""
    # Setup
    mock_use_cases.get_parking_spot_by_coordinates.return_value = [sample_parking]

    # Execute
    response = client.get(
        "/api/v1/mos_parking/parking",
        params={"lat": 55.7558, "long": 37.6176, "distance": 1000, "limit": 5},
    )

    # Verify
    assert response.status_code == 200
    data = response.json()
    assert len(data) == 1
    assert data[0]["_id"] == 1

    mock_use_cases.get_parking_spot_by_coordinates.assert_called_once()


def test_search_parkings_by_coords_empty(client, mock_use_cases):
    """Tests parking search by coordinates without results."""
    # Setup
    mock_use_cases.get_parking_spot_by_coordinates.return_value = []

    # Execute
    response = client.get(
        "/api/v1/mos_parking/parking",
        params={"lat": 55.7558, "long": 37.6176, "distance": 1000, "limit": 5},
    )

    # Verify
    assert response.status_code == 404
    data = response.json()
    assert data["detail"]["error"] == "Not Found Error"


def test_get_parking_by_id_success(client, mock_use_cases, sample_parking):
    """Tests successful parking retrieval by ID."""
    # Setup
    mock_use_cases.get_parking_by_id.return_value = sample_parking

    # Execute
    response = client.get("/api/v1/mos_parking/parking/1")

    # Verify
    assert response.status_code == 200
    data = response.json()
    assert data["_id"] == 1

    mock_use_cases.get_parking_by_id.assert_called_once_with(1)


def test_get_parking_by_id_not_found(client, mock_use_cases):
    """Tests retrieval of non-existent parking by ID."""
    # Setup
    mock_use_cases.get_parking_by_id.return_value = None

    # Execute
    response = client.get("/api/v1/mos_parking/parking/999")

    # Verify
    assert response.status_code == 404
    data = response.json()
    assert data["detail"]["error"] == "Not Found Error"


def test_search_parkings_by_name_success(client, mock_use_cases, sample_parking):
    """Tests successful parking search by name."""
    # Setup
    mock_use_cases.get_parking_by_name.return_value = [sample_parking]

    # Execute
    response = client.get("/api/v1/mos_parking/parking/search", params={"name": "Test"})

    # Verify
    assert response.status_code == 200
    data = response.json()
    assert len(data) == 1

    mock_use_cases.get_parking_by_name.assert_called_once()


def test_search_parkings_by_name_not_found(client, mock_use_cases):
    """Tests parking search by name without results."""
    # Setup
    mock_use_cases.get_parking_by_name.return_value = []

    # Execute
    response = client.get(
        "/api/v1/mos_parking/parking/search", params={"name": "Nonexistent"}
    )

    # Verify
    assert response.status_code == 404
    data = response.json()
    assert data["detail"]["error"] == "Not Found Error"


# Tests for address search removed as such endpoint doesn't exist in current API


def test_sync_parking_data_success(client, mock_use_cases):
    """Tests successful parking data synchronization."""
    # Setup
    mock_use_cases.save_or_update_parking_spots.return_value = None

    # Execute
    response = client.post("/api/v1/mos_parking/sync")

    # Verify
    assert response.status_code == 200
    data = response.json()
    assert data["status"] == "success"
    assert "synchronization completed successfully" in data["message"]

    mock_use_cases.save_or_update_parking_spots.assert_called_once()


def test_sync_parking_data_error(client, mock_use_cases):
    """Tests parking data synchronization with error."""
    # Setup
    mock_use_cases.save_or_update_parking_spots.side_effect = Exception("Sync failed")

    # Execute
    response = client.post("/api/v1/mos_parking/sync")

    # Verify
    assert response.status_code == 500
    data = response.json()
    assert data["detail"]["error"] == "Internal Server Error"
