"""Main application - HTTP server."""

import sys
from contextlib import asynccontextmanager
from typing import Any

import structlog
import uvicorn
from fastapi import FastAPI

from parking.api.http_server import setup_routes
from parking.application.config import ServiceConfig
from parking.application.use_cases import UseCases
from parking.infrastructure.http_parking_data_source import HttpParkingDataSource
from parking.infrastructure.logging import init_logger
from parking.infrastructure.mongodb_storage import MongoDBStorage

logger: structlog.typing.FilteringBoundLogger


@asynccontextmanager
async def lifespan(app: FastAPI) -> Any:
    """Application lifecycle management."""
    global logger

    # Load configuration
    try:
        config = ServiceConfig()
    except Exception as e:
        print(f"Failed to load configuration: {e}", file=sys.stderr)
        sys.exit(1)

    # Initialize logger
    logger = init_logger(config.logger.format)
    logger.info("App starting...")

    # Connect to dependencies
    try:
        storage = await MongoDBStorage.connect(config.mongodb)
        data_source = HttpParkingDataSource(config.parking_data_source)

        # Create use cases and save in application state
        use_cases = UseCases(storage, data_source)
        app.state.use_cases = use_cases
        app.state.storage = storage
        app.state.data_source = data_source

        logger.info("App started successfully")
        yield

    except Exception as e:
        logger.error("Failed to start app", error=str(e))
        sys.exit(1)

    # Close connections
    logger.info("App shutting down...")
    await app.state.storage.close()
    await app.state.data_source.close()
    logger.info("App shut down")


def create_main_app() -> FastAPI:
    """Creates main FastAPI application with lifecycle management."""
    # Create application with lifespan
    app = FastAPI(
        title="Parking",
        description="Microservice for working with Moscow parking data",
        version="0.1.0",
        redoc_url=None,
        lifespan=lifespan,
    )

    # Setup routes without creating through create_app
    setup_routes(app)

    return app


app = create_main_app()


def main() -> None:
    """Starts HTTP server."""
    try:
        config = ServiceConfig()
    except Exception as e:
        print(f"Failed to load configuration: {e}", file=sys.stderr)
        sys.exit(1)

    uvicorn.run(
        "parking.main:app",
        host=config.http_server.host,
        port=config.http_server.port,
        reload=False,
        access_log=False,
    )


if __name__ == "__main__":
    main()
