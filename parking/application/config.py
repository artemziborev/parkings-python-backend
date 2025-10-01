"""Application configuration."""

from typing import Literal

from pydantic import Field
from pydantic_settings import BaseSettings, SettingsConfigDict


class LoggerConfig(BaseSettings):
    """Logging configuration."""

    format: Literal["json", "pretty"] = Field(
        default="pretty", description="Log format"
    )


class HttpServerConfig(BaseSettings):
    """HTTP server configuration."""

    host: str = Field(default="0.0.0.0", description="Server host")
    port: int = Field(default=3847, description="Server port")

    @property
    def address(self) -> str:
        """Returns full server address."""
        return f"{self.host}:{self.port}"


class CORSConfig(BaseSettings):
    """CORS configuration."""

    allow_origins: list[str] = Field(
        default=["*"], description="Allowed origins for CORS"
    )
    allow_credentials: bool = Field(
        default=True, description="Allow credentials in CORS"
    )
    allow_methods: list[str] = Field(default=["*"], description="Allowed HTTP methods")
    allow_headers: list[str] = Field(default=["*"], description="Allowed headers")


class SearchConfig(BaseSettings):
    """Search configuration."""

    default_limit: int = Field(default=20, description="Default search results limit")
    max_limit: int = Field(default=100, description="Maximum search results limit")
    earth_radius_meters: int = Field(
        default=6371000, description="Earth radius in meters for distance calculations"
    )


class MongoDBConfig(BaseSettings):
    """MongoDB configuration."""

    address: str = Field(..., description="MongoDB address")
    username: str = Field(default="", description="Username")
    password: str = Field(default="", description="Password")
    database: str = Field(..., description="Database name")
    collection: str = Field(default="parkings", description="Collection name")
    expired_secs: int = Field(default=7776000, description="Document TTL")

    @property
    def connection_string(self) -> str:
        """Returns MongoDB connection string."""
        if self.username and self.password:
            return f"mongodb://{self.username}:{self.password}@{self.address}/{self.database}?authSource=admin"
        else:
            return f"mongodb://{self.address}/{self.database}"


class ParkingDataSourceConfig(BaseSettings):
    """Parking data source configuration."""

    url: str = Field(..., description="API URL for data loading")
    timeout_secs: int = Field(default=60, description="Request timeout in seconds")


class FileDataSourceConfig(BaseSettings):
    """File data source configuration."""

    path: str = Field(default="./dump.json", description="Path to data file")


class ServiceConfig(BaseSettings):
    """Main service configuration."""

    model_config = SettingsConfigDict(
        env_file=".env",
        env_file_encoding="utf-8",
        env_nested_delimiter="__",
        case_sensitive=False,
    )

    logger: LoggerConfig = Field(default_factory=LoggerConfig)
    http_server: HttpServerConfig = Field(default_factory=HttpServerConfig)
    cors: CORSConfig = Field(default_factory=CORSConfig)
    search: SearchConfig = Field(default_factory=SearchConfig)
    mongodb: MongoDBConfig = Field(
        default_factory=lambda: MongoDBConfig(
            address="localhost:27017", database="parking"
        )
    )
    parking_data_source: ParkingDataSourceConfig = Field(
        default_factory=lambda: ParkingDataSourceConfig(
            url="https://apidata.mos.ru/opendata/7710881420-parking/data"
        )
    )
    file_data_source: FileDataSourceConfig = Field(default_factory=FileDataSourceConfig)
