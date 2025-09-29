"""MongoDB parking storage implementation."""

from typing import List, Optional, Dict, Any

import structlog
from motor.motor_asyncio import AsyncIOMotorClient, AsyncIOMotorCollection
from pymongo import GEOSPHERE
from pymongo.errors import DuplicateKeyError

from parking.application.interfaces import ParkingStorage
from parking.domain.models import ActiveParkings, Coordinates, Parking
from parking.infrastructure.config import MongoDBConfig


logger = structlog.get_logger()


class MongoDBStorage(ParkingStorage):
    """MongoDB parking storage implementation."""
    
    def __init__(
        self,
        client: AsyncIOMotorClient[Dict[str, Any]],
        config: MongoDBConfig,
    ) -> None:
        self._client = client
        self._config = config
        self._collection: AsyncIOMotorCollection[Dict[str, Any]] = (
            client[config.database][config.collection]
        )
    
    @classmethod
    async def connect(cls, config: MongoDBConfig) -> "MongoDBStorage":
        """Creates MongoDB connection."""
        client = AsyncIOMotorClient(config.connection_string)
        
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
            await self._collection.create_index([
                ("name.ru", "text"), ("name.en", "text"),
                ("address.street.ru", "text"), ("address.street.en", "text"),
                ("address.house.ru", "text"), ("address.house.en", "text"),
                ("subway.ru", "text"), ("subway.en", "text"),
                ("description.ru", "text"), ("description.en", "text")
            ])
            
            # Index for search by number/litera
            await self._collection.create_index("litera")
            
            logger.info("MongoDB indexes ensured")
        except DuplicateKeyError:
            # Indexes already exist
            pass
    
    async def upsert(self, active_parkings: ActiveParkings) -> None:
        """Saves or updates active parkings."""
        if active_parkings.is_empty():
            logger.warning("No active parkings to upsert")
            return
        
        # Convert parkings to MongoDB documents
        documents = []
        for parking in active_parkings:
            doc = parking.model_dump(by_alias=True)
            documents.append(doc)
        
        # Remove old data and insert new data
        await self._collection.delete_many({})
        await self._collection.insert_many(documents)
        
        logger.info("Upserted parkings", count=len(documents))
    
    async def find_by_coordinates(
        self,
        coords: Coordinates,
        distance: int,
        limit: int,
    ) -> List[Parking]:
        """Finds parkings by coordinates within given radius."""
        # Use $near for GeoJSON points
        query = {
            "center": {
                "$near": {
                    "$geometry": {
                        "type": "Point",
                        "coordinates": [coords.longitude, coords.latitude]
                    },
                    "$maxDistance": distance
                }
            }
        }
        
        cursor = self._collection.find(query).limit(limit)
        documents = await cursor.to_list(length=limit)
        
        parkings = []
        for doc in documents:
            # Calculate distance manually
            parking_coords = doc.get("center", {}).get("coordinates", [])
            if len(parking_coords) == 2:
                from math import radians, cos, sin, asin, sqrt
                
                def haversine(lon1, lat1, lon2, lat2):
                    """Calculate the great circle distance between two points on Earth."""
                    lon1, lat1, lon2, lat2 = map(radians, [lon1, lat1, lon2, lat2])
                    dlon = lon2 - lon1
                    dlat = lat2 - lat1
                    a = sin(dlat/2)**2 + cos(lat1) * cos(lat2) * sin(dlon/2)**2
                    c = 2 * asin(sqrt(a))
                    # Use Earth radius from configuration
                    from parking.infrastructure.config import ServiceConfig
                    config = ServiceConfig()
                    r = config.search.earth_radius_meters
                    return c * r
                
                distance_m = haversine(
                    coords.longitude, coords.latitude,
                    parking_coords[0], parking_coords[1]
                )
                doc["distance"] = distance_m
            
            parking = Parking.model_validate(doc)
            parkings.append(parking)
        
        # Sort by distance
        parkings.sort(key=lambda x: getattr(x, 'distance', float('inf')))
        
        return parkings
    
    async def find_by_id(self, parking_id: int) -> Optional[Parking]:
        """Finds parking by ID."""
        doc = await self._collection.find_one({"_id": parking_id})
        
        if doc is None:
            return None
        
        return Parking.model_validate(doc)
    
    async def find_by_name(self, name: str, limit: int) -> List[Parking]:
        """Finds parkings by name with partial search support."""
        # First try full-text search
        cursor = self._collection.find(
            {"$text": {"$search": name}},
        ).limit(limit)
        
        documents = await cursor.to_list(length=limit)
        
        # If full-text search didn't return results, use regex
        if not documents:
            search_pattern = {"$regex": name, "$options": "i"}
            cursor = self._collection.find({
                "$or": [
                    {"name.ru": search_pattern},
                    {"name.en": search_pattern},
                    {"address.street.ru": search_pattern},
                    {"address.street.en": search_pattern},
                    {"subway.ru": search_pattern},
                    {"subway.en": search_pattern},
                    {"description.ru": search_pattern},
                    {"description.en": search_pattern}
                ]
            }).limit(limit)
            documents = await cursor.to_list(length=limit)
        
        parkings = []
        for doc in documents:
            parking = Parking.model_validate(doc)
            parkings.append(parking)
        
        return parkings
    
    async def find_by_name_and_number(
        self,
        name: Optional[str],
        number: Optional[str],
        limit: int,
    ) -> List[Parking]:
        """Finds parkings by name and/or number with partial search support."""
        query: Dict[str, Any] = {}
        or_conditions = []
        
        if name:
            # First try full-text search
            text_query = {"$text": {"$search": name}}
            cursor = self._collection.find(text_query).limit(limit)
            documents = await cursor.to_list(length=limit)
            
            # If full-text search didn't return results, use regex
            if not documents:
                search_pattern = {"$regex": name, "$options": "i"}
                or_conditions.extend([
                    {"name.ru": search_pattern},
                    {"name.en": search_pattern},
                    {"address.street.ru": search_pattern},
                    {"address.street.en": search_pattern},
                    {"subway.ru": search_pattern},
                    {"subway.en": search_pattern},
                    {"description.ru": search_pattern},
                    {"description.en": search_pattern},
                    {"zone.number": search_pattern}
                ])
            else:
                # If text search returned results, add condition for number
                if number:
                    query["litera"] = {"$regex": number, "$options": "i"}
                    cursor = self._collection.find(query).limit(limit)
                    documents = await cursor.to_list(length=limit)
                
                parkings = []
                for doc in documents:
                    parking = Parking.model_validate(doc)
                    parkings.append(parking)
                
                return parkings
        
        if number:
            or_conditions.append({"litera": {"$regex": number, "$options": "i"}})
            or_conditions.append({"zone.number": {"$regex": number, "$options": "i"}})
        
        if or_conditions:
            query["$or"] = or_conditions
            cursor = self._collection.find(query).limit(limit)
            documents = await cursor.to_list(length=limit)
        else:
            # If no search conditions, return empty result
            documents = []
        
        parkings = []
        for doc in documents:
            parking = Parking.model_validate(doc)
            parkings.append(parking)
        
        return parkings
    
    async def find_by_address(self, address_query: str, limit: int) -> List[Parking]:
        """Finds parkings by address with partial search support."""
        search_pattern = {"$regex": address_query, "$options": "i"}
        
        cursor = self._collection.find({
            "$or": [
                {"address.street.ru": search_pattern},
                {"address.street.en": search_pattern},
                {"address.house.ru": search_pattern},
                {"address.house.en": search_pattern},
                {"resolutionAddress": search_pattern}
            ]
        }).limit(limit)
        
        documents = await cursor.to_list(length=limit)
        
        parkings = []
        for doc in documents:
            parking = Parking.model_validate(doc)
            parkings.append(parking)
        
        return parkings
    
    async def find_all(self, limit: Optional[int] = None) -> List[Parking]:
        """Gets all parkings with optional limit."""
        try:
            cursor = self._collection.find({})
            
            if limit:
                cursor = cursor.limit(limit)
            
            documents = await cursor.to_list(length=None)
            parkings = [Parking.model_validate(doc) for doc in documents]
            
            logger.info("Found all parkings", count=len(parkings))
            return parkings
            
        except Exception as e:
            logger.error("Error finding all parkings", error=str(e))
            return []
    
    async def close(self) -> None:
        """Closes MongoDB connection."""
        self._client.close()
        logger.info("MongoDB connection closed")
