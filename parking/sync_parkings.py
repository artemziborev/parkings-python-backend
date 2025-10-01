"""Parking data synchronization utility."""

import asyncio
import sys
from typing import NoReturn

from parking.application.config import ServiceConfig
from parking.application.use_cases import UseCases
from parking.infrastructure.http_parking_data_source import HttpParkingDataSource
from parking.infrastructure.logging import init_logger
from parking.infrastructure.mongodb_storage import MongoDBStorage


async def sync_parkings() -> None:
    """Synchronizes parking data."""
    # Load configuration
    try:
        config = ServiceConfig()
    except Exception as e:
        print(f"Failed to load configuration: {e}", file=sys.stderr)
        sys.exit(1)

    # Initialize logger
    logger = init_logger(config.logger.format)
    logger.info("Starting parking data synchronization job")

    # Connect to dependencies
    try:
        storage = await MongoDBStorage.connect(config.mongodb)
        data_source = HttpParkingDataSource(config.parking_data_source)

        logger.info("Using data source URL", url=config.parking_data_source.url)

        # Create use cases and run synchronization
        use_cases = UseCases(storage, data_source)
        await use_cases.save_or_update_parking_spots()

        logger.info("Parking data synchronization completed successfully")

    except Exception as e:
        logger.error("Parking data synchronization failed", error=str(e))
        raise

    finally:
        # Close connections
        if "storage" in locals():
            await storage.close()
        if "data_source" in locals():
            await data_source.close()


def main() -> NoReturn:
    """Starts parking synchronization."""
    try:
        asyncio.run(sync_parkings())
        sys.exit(0)
    except Exception as e:
        print(f"Synchronization failed: {e}", file=sys.stderr)
        sys.exit(1)


if __name__ == "__main__":
    main()
