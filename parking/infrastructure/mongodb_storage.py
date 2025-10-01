"""MongoDB parking storage implementation."""

from typing import Any

import structlog
from motor.motor_asyncio import AsyncIOMotorClient, AsyncIOMotorCollection
from pymongo import GEOSPHERE
from pymongo.errors import DuplicateKeyError

from parking.application.config import MongoDBConfig
from parking.domain.interfaces import ParkingStorage
from parking.domain.models import ActiveParkings, Coordinates, Parking

logger = structlog.get_logger()


class MongoDBStorage(ParkingStorage):
    """MongoDB parking storage implementation."""

    def __init__(
        self,
        client: AsyncIOMotorClient[dict[str, Any]],
        config: MongoDBConfig,
    ) -> None:
        self._client = client
        self._config = config
        self._collection: AsyncIOMotorCollection[dict[str, Any]] = client[
            config.database
        ][config.collection]

    @classmethod
    async def connect(cls, config: MongoDBConfig) -> "MongoDBStorage":
        """Creates MongoDB connection."""
        client: AsyncIOMotorClient[dict[str, Any]] = AsyncIOMotorClient(
            config.connection_string
        )

        # Test connection
        await client.admin.command("ping")
        logger.info("Connected to MongoDB", database=config.database)

        storage = cls(client, config)
        await storage._ensure_indexes()
        return storage

    async def _ensure_indexes(self) -> None:
        """Creates necessary indexes."""
        try:
            # Geospatial index for coordinate search
            await self._collection.create_index([("center", GEOSPHERE)])

            # Extended text index for search by name, address and metro
            await self._collection.create_index(
                [
                    ("name.ru", "text"),
                    ("name.en", "text"),
                    ("address.street.ru", "text"),
                    ("address.street.en", "text"),
                    ("address.house.ru", "text"),
                    ("address.house.en", "text"),
                    ("subway.ru", "text"),
                    ("subway.en", "text"),
                    ("description.ru", "text"),
                    ("description.en", "text"),
                ]
            )

            # Index for search by number/litera
            await self._collection.create_index("litera")

            logger.info("MongoDB indexes ensured")
        except DuplicateKeyError:
            # Indexes already exist
            pass

    def _convert_parkings_to_documents(
        self, active_parkings: ActiveParkings
    ) -> list[dict[str, Any]]:
        """Converts parkings to MongoDB documents."""
        documents = []
        for parking in active_parkings:
            doc = parking.model_dump(by_alias=True)
            documents.append(doc)
        return documents

    async def _clear_collection(self) -> None:
        """Clears all documents from the collection."""
        await self._collection.delete_many({})
        logger.debug("Cleared collection")

    async def _insert_documents(self, documents: list[dict[str, Any]]) -> None:
        """Inserts documents into the collection."""
        if not documents:
            logger.warning("No documents to insert")
            return

        await self._collection.insert_many(documents)
        logger.debug("Inserted documents", count=len(documents))

    async def upsert(self, active_parkings: ActiveParkings) -> None:
        """Saves or updates active parkings."""
        if active_parkings.is_empty():
            logger.warning("No active parkings to upsert")
            return

        # Convert parkings to MongoDB documents
        documents = self._convert_parkings_to_documents(active_parkings)

        # Remove old data and insert new data
        await self._clear_collection()
        await self._insert_documents(documents)

        logger.info("Upserted parkings", count=len(documents))

    def _build_geospatial_query(
        self, coords: Coordinates, distance: int
    ) -> dict[str, Any]:
        """Builds MongoDB geospatial query for coordinate search."""
        return {
            "center": {
                "$near": {
                    "$geometry": {
                        "type": "Point",
                        "coordinates": [coords.longitude, coords.latitude],
                    },
                    "$maxDistance": distance,
                }
            }
        }

    def _calculate_distance(
        self, coords: Coordinates, parking_coords: list[float]
    ) -> float:
        """Calculates distance between two coordinates using Haversine formula."""
        from math import asin, cos, radians, sin, sqrt

        def haversine(lon1: float, lat1: float, lon2: float, lat2: float) -> float:
            """Calculate the great circle distance between two points on Earth."""
            lon1, lat1, lon2, lat2 = map(radians, [lon1, lat1, lon2, lat2])
            dlon = lon2 - lon1
            dlat = lat2 - lat1
            a = sin(dlat / 2) ** 2 + cos(lat1) * cos(lat2) * sin(dlon / 2) ** 2
            c = 2 * asin(sqrt(a))
            # Use Earth radius from configuration
            from parking.application.config import ServiceConfig

            config = ServiceConfig()
            r = config.search.earth_radius_meters
            return c * r

        return haversine(
            coords.longitude, coords.latitude, parking_coords[0], parking_coords[1]
        )

    def _add_distance_to_documents(
        self, documents: list[dict[str, Any]], coords: Coordinates
    ) -> None:
        """Adds calculated distance to documents."""
        for doc in documents:
            parking_coords = doc.get("center", {}).get("coordinates", [])
            if len(parking_coords) == 2:
                distance_m = self._calculate_distance(coords, parking_coords)
                doc["distance"] = distance_m

    def _convert_documents_to_parkings(
        self, documents: list[dict[str, Any]]
    ) -> list[Parking]:
        """Converts MongoDB documents to Parking objects."""
        parkings = []
        for doc in documents:
            try:
                parking = Parking.model_validate(doc)
                parkings.append(parking)
            except Exception as e:
                logger.warning(
                    "Failed to convert document to Parking",
                    doc_id=doc.get("_id"),
                    error=str(e),
                )
                continue
        return parkings

    def _sort_parkings_by_distance(self, parkings: list[Parking]) -> list[Parking]:
        """Sorts parkings by distance."""
        parkings.sort(key=lambda x: getattr(x, "distance", float("inf")))
        return parkings

    async def find_by_coordinates(
        self,
        coords: Coordinates,
        distance: int,
        limit: int,
    ) -> list[Parking]:
        """Finds parkings by coordinates within given radius."""
        # Build geospatial query
        query = self._build_geospatial_query(coords, distance)

        # Execute query
        cursor = self._collection.find(query).limit(limit)
        documents = await cursor.to_list(length=limit)

        # Add calculated distances to documents
        self._add_distance_to_documents(documents, coords)

        # Convert to Parking objects
        parkings = self._convert_documents_to_parkings(documents)

        # Sort by distance
        return self._sort_parkings_by_distance(parkings)

    async def find_by_id(self, parking_id: int) -> Parking | None:
        """Finds parking by ID."""
        doc = await self._collection.find_one({"_id": parking_id})

        if doc is None:
            return None

        parkings = self._convert_documents_to_parkings([doc])
        return parkings[0] if parkings else None

    async def find_by_name(self, name: str, limit: int) -> list[Parking]:
        """Finds parkings by name with partial search support."""
        # First try full-text search
        cursor = self._collection.find(
            {"$text": {"$search": name}},
        ).limit(limit)

        documents = await cursor.to_list(length=limit)

        # If full-text search didn't return results, use regex
        if not documents:
            search_pattern = {"$regex": name, "$options": "i"}
            cursor = self._collection.find(
                {
                    "$or": [
                        {"name.ru": search_pattern},
                        {"name.en": search_pattern},
                        {"address.street.ru": search_pattern},
                        {"address.street.en": search_pattern},
                        {"subway.ru": search_pattern},
                        {"subway.en": search_pattern},
                        {"description.ru": search_pattern},
                        {"description.en": search_pattern},
                    ]
                }
            ).limit(limit)
            documents = await cursor.to_list(length=limit)

        return self._convert_documents_to_parkings(documents)

    def _build_name_search_conditions(self, name: str) -> list[dict[str, Any]]:
        """Builds search conditions for name search."""
        search_pattern = {"$regex": name, "$options": "i"}
        return [
            {"name.ru": search_pattern},
            {"name.en": search_pattern},
            {"address.street.ru": search_pattern},
            {"address.street.en": search_pattern},
            {"subway.ru": search_pattern},
            {"subway.en": search_pattern},
            {"description.ru": search_pattern},
            {"description.en": search_pattern},
            {"zone.number": search_pattern},
        ]

    def _build_number_search_conditions(self, number: str) -> list[dict[str, Any]]:
        """Builds search conditions for number search."""
        search_pattern = {"$regex": number, "$options": "i"}
        return [{"litera": search_pattern}, {"zone.number": search_pattern}]

    async def _search_by_text(self, name: str, limit: int) -> list[dict[str, Any]]:
        """Searches by full-text index."""
        cursor = self._collection.find({"$text": {"$search": name}}).limit(limit)
        return await cursor.to_list(length=limit)

    async def _search_by_regex(
        self, conditions: list[dict[str, Any]], limit: int
    ) -> list[dict[str, Any]]:
        """Searches by regex patterns."""
        query = {"$or": conditions}
        cursor = self._collection.find(query).limit(limit)
        return await cursor.to_list(length=limit)

    async def find_by_name_and_number(
        self,
        name: str | None,
        number: str | None,
        limit: int,
    ) -> list[Parking]:
        """Finds parkings by name and/or number with partial search support."""
        if not name and not number:
            return []

        documents = []

        if name:
            # First try full-text search
            documents = await self._search_by_text(name, limit)

            # If full-text search didn't return results, use regex
            if not documents:
                name_conditions = self._build_name_search_conditions(name)
                documents = await self._search_by_regex(name_conditions, limit)
            else:
                # If text search returned results and we have number, filter by number
                if number:
                    number_conditions = self._build_number_search_conditions(number)
                    query = {
                        "$and": [
                            {"$text": {"$search": name}},
                            {"$or": number_conditions},
                        ]
                    }
                    cursor = self._collection.find(query).limit(limit)
                    documents = await cursor.to_list(length=limit)

        if not documents and number:
            # Search only by number
            number_conditions = self._build_number_search_conditions(number)
            documents = await self._search_by_regex(number_conditions, limit)

        return self._convert_documents_to_parkings(documents)

    async def find_by_address(self, address_query: str, limit: int) -> list[Parking]:
        """Finds parkings by address with partial search support."""
        search_pattern = {"$regex": address_query, "$options": "i"}

        cursor = self._collection.find(
            {
                "$or": [
                    {"address.street.ru": search_pattern},
                    {"address.street.en": search_pattern},
                    {"address.house.ru": search_pattern},
                    {"address.house.en": search_pattern},
                    {"resolutionAddress": search_pattern},
                ]
            }
        ).limit(limit)

        documents = await cursor.to_list(length=limit)

        return self._convert_documents_to_parkings(documents)

    async def find_all(self, limit: int | None = None) -> list[Parking]:
        """Gets all parkings with optional limit."""
        try:
            cursor = self._collection.find({})

            if limit:
                cursor = cursor.limit(limit)

            documents = await cursor.to_list(length=None)
            parkings = self._convert_documents_to_parkings(documents)

            logger.info("Found all parkings", count=len(parkings))
            return parkings

        except Exception as e:
            logger.error("Error finding all parkings", error=str(e))
            return []

    async def close(self) -> None:
        """Closes MongoDB connection."""
        self._client.close()
        logger.info("MongoDB connection closed")
