"""Tests for configuration."""

import os

from parking.application.config import (
    CORSConfig,
    FileDataSourceConfig,
    HttpServerConfig,
    LoggerConfig,
    MongoDBConfig,
    ParkingDataSourceConfig,
    SearchConfig,
    ServiceConfig,
)


def test_logger_config_defaults():
    """Tests default values for LoggerConfig."""
    config = LoggerConfig()
    assert config.format == "pretty"


def test_http_server_config_defaults():
    """Tests default values for HttpServerConfig."""
    config = HttpServerConfig()
    assert config.host == "0.0.0.0"
    assert config.port == 3847
    assert config.address == "0.0.0.0:3847"


def test_http_server_config_custom():
    """Tests custom values for HttpServerConfig."""
    config = HttpServerConfig(host="127.0.0.1", port=8000)
    assert config.host == "127.0.0.1"
    assert config.port == 8000
    assert config.address == "127.0.0.1:8000"


def test_mongodb_config():
    """Tests MongoDBConfig."""
    config = MongoDBConfig(
        address="localhost:27017", username="user", password="pass", database="testdb"
    )
    assert config.address == "localhost:27017"
    assert config.username == "user"
    assert config.password == "pass"
    assert config.database == "testdb"
    assert config.collection == "parkings"
    assert config.expired_secs == 7776000
    assert (
        config.connection_string
        == "mongodb://user:pass@localhost:27017/testdb?authSource=admin"
    )


def test_mongodb_config_custom_collection():
    """Tests MongoDBConfig with custom collection."""
    config = MongoDBConfig(
        address="localhost:27017",
        username="user",
        password="pass",
        database="testdb",
        collection="custom_parkings",
    )
    assert config.collection == "custom_parkings"


def test_parking_data_source_config():
    """Tests ParkingDataSourceConfig."""
    config = ParkingDataSourceConfig(url="https://example.com/api")
    assert config.url == "https://example.com/api"
    assert config.timeout_secs == 60


def test_parking_data_source_config_custom_timeout():
    """Tests ParkingDataSourceConfig with custom timeout."""
    config = ParkingDataSourceConfig(url="https://example.com/api", timeout_secs=120)
    assert config.timeout_secs == 120


def test_file_data_source_config_defaults():
    """Tests default values for FileDataSourceConfig."""
    # Pass explicit path value due to pydantic-settings specifics
    # which may pick up environment variables
    config = FileDataSourceConfig(path="./dump.json")
    assert config.path == "./dump.json"


def test_file_data_source_config_custom():
    """Tests custom path for FileDataSourceConfig."""
    config = FileDataSourceConfig(path="/tmp/data.json")
    assert config.path == "/tmp/data.json"


def test_cors_config_defaults():
    """Tests default values for CORSConfig."""
    config = CORSConfig()
    assert config.allow_origins == ["*"]
    assert config.allow_credentials is True
    assert config.allow_methods == ["*"]
    assert config.allow_headers == ["*"]


def test_cors_config_custom():
    """Tests custom values for CORSConfig."""
    config = CORSConfig(
        allow_origins=["http://localhost:3000", "https://example.com"],
        allow_credentials=False,
        allow_methods=["GET", "POST"],
        allow_headers=["Content-Type", "Authorization"],
    )
    assert config.allow_origins == ["http://localhost:3000", "https://example.com"]
    assert config.allow_credentials is False
    assert config.allow_methods == ["GET", "POST"]
    assert config.allow_headers == ["Content-Type", "Authorization"]


def test_search_config_defaults():
    """Tests default values for SearchConfig."""
    config = SearchConfig()
    assert config.default_limit == 20
    assert config.max_limit == 100
    assert config.earth_radius_meters == 6371000


def test_search_config_custom():
    """Tests custom values for SearchConfig."""
    config = SearchConfig(default_limit=50, max_limit=200, earth_radius_meters=6378137)
    assert config.default_limit == 50
    assert config.max_limit == 200
    assert config.earth_radius_meters == 6378137


def test_service_config_with_environment_variables():
    """Tests ServiceConfig with environment variables."""
    # Set environment variables
    os.environ.update(
        {
            "LOGGER__FORMAT": "json",
            "HTTP_SERVER__HOST": "127.0.0.1",
            "HTTP_SERVER__PORT": "8000",
            "CORS__ALLOW_ORIGINS": '["http://localhost:3000"]',
            "SEARCH__DEFAULT_LIMIT": "50",
            "MONGODB__ADDRESS": "test-mongo:27017",
            "MONGODB__DATABASE": "test_db",
            "PARKING_DATA_SOURCE__URL": "https://test-api.com/parkings",
        }
    )

    try:
        config = ServiceConfig()
        assert config.logger.format == "json"
        assert config.http_server.host == "127.0.0.1"
        assert config.http_server.port == 8000
        assert config.cors.allow_origins == ["http://localhost:3000"]
        assert config.search.default_limit == 50
        assert config.mongodb.address == "test-mongo:27017"
        assert config.mongodb.database == "test_db"
        assert config.parking_data_source.url == "https://test-api.com/parkings"
    finally:
        # Clean up environment variables
        for key in [
            "LOGGER__FORMAT",
            "HTTP_SERVER__HOST",
            "HTTP_SERVER__PORT",
            "CORS__ALLOW_ORIGINS",
            "SEARCH__DEFAULT_LIMIT",
            "MONGODB__ADDRESS",
            "MONGODB__DATABASE",
            "PARKING_DATA_SOURCE__URL",
        ]:
            os.environ.pop(key, None)
