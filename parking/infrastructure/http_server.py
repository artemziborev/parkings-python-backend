"""FastAPI HTTP server."""

from typing import List, Optional, Annotated

import structlog
from fastapi import FastAPI, HTTPException, Query, Path, Depends
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel, Field

from parking.application.use_cases import UseCases
from parking.domain.models import Coordinates, Parking


logger = structlog.get_logger()


# Request/Response models
class ErrorResponse(BaseModel):
    """Error response."""
    
    error: str = Field(..., description="Error type")
    details: str = Field(..., description="Error details")


def setup_routes(app: FastAPI) -> None:
    """Sets up routes for FastAPI application."""
    
    # CORS middleware - settings are taken from configuration
    from parking.infrastructure.config import ServiceConfig
    config = ServiceConfig()
    
    app.add_middleware(
        CORSMiddleware,
        allow_origins=config.cors.allow_origins,
        allow_credentials=config.cors.allow_credentials,
        allow_methods=config.cors.allow_methods,
        allow_headers=config.cors.allow_headers,
    )
    
    def get_use_cases() -> UseCases:
        """Gets use_cases from application state."""
        return app.state.use_cases
    
    @app.get(
        "/api/v1/mos_parking/parking",
        response_model=List[Parking],
        responses={
            404: {"model": ErrorResponse, "description": "Parkings not found"},
            500: {"model": ErrorResponse, "description": "Internal server error"},
        },
        tags=["parking"],
        summary="Search parkings by coordinates",
    )
    async def get_parking_info(
        lat: Annotated[float, Query(description="Latitude")],
        long: Annotated[float, Query(description="Longitude")],
        distance: Annotated[int, Query(description="Search radius in meters")],
        limit: Annotated[int, Query(description="Maximum number of results")],
    ) -> List[Parking]:
        """Searches for parkings within given radius from coordinates."""
        try:
            use_cases = get_use_cases()
            coordinates = Coordinates(latitude=lat, longitude=long)
            parkings = await use_cases.get_parking_spot_by_coordinates(
                coordinates, distance, limit
            )
            
            if not parkings:
                raise HTTPException(
                    status_code=404,
                    detail={
                        "error": "Not Found Error",
                        "details": "Parking space not found",
                    },
                )
            
            return parkings
            
        except HTTPException:
            raise
        except Exception as e:
            logger.error("Error searching parkings by coordinates", error=str(e))
            raise HTTPException(
                status_code=500,
                detail={"error": "Internal Server Error", "details": str(e)},
            )
    
    @app.get(
        "/api/v1/mos_parking/parking/search",
        response_model=List[Parking],
        responses={
            404: {"model": ErrorResponse, "description": "Parkings not found"},
            500: {"model": ErrorResponse, "description": "Internal server error"},
        },
        tags=["parking"],
        summary="Search parkings by name",
    )
    async def search_parking_by_name(
        name: Annotated[str, Query(description="Parking name")],
        limit: Annotated[Optional[int], Query(description="Maximum number of results")] = None,
    ) -> List[Parking]:
        """Searches for parkings by name."""
        try:
            use_cases = get_use_cases()
            # Use default limit from configuration if not specified
            if limit is None:
                limit = config.search.default_limit
            parkings = await use_cases.get_parking_by_name(name, limit)
            
            if not parkings:
                raise HTTPException(
                    status_code=404,
                    detail={
                        "error": "Not Found Error",
                        "details": "No parkings found with specified name",
                    },
                )
            
            return parkings
            
        except HTTPException:
            raise
        except Exception as e:
            logger.error("Error searching parkings by name", name=name, error=str(e))
            raise HTTPException(
                status_code=500,
                detail={"error": "Internal Server Error", "details": str(e)},
            )
    
    @app.get(
        "/api/v1/mos_parking/parking/{id}",
        response_model=Parking,
        responses={
            404: {"model": ErrorResponse, "description": "Parking not found"},
            500: {"model": ErrorResponse, "description": "Internal server error"},
        },
        tags=["parking"],
        summary="Get parking by ID",
    )
    async def get_parking_by_id(
        id: Annotated[int, Path(description="Parking ID")],
    ) -> Parking:
        """Gets parking by ID."""
        try:
            use_cases = get_use_cases()
            parking = await use_cases.get_parking_by_id(id)
            
            if parking is None:
                raise HTTPException(
                    status_code=404,
                    detail={
                        "error": "Not Found Error",
                        "details": "Parking with specified ID not found",
                    },
                )
            
            return parking
            
        except HTTPException:
            raise
        except Exception as e:
            logger.error("Error getting parking by ID", parking_id=id, error=str(e))
            raise HTTPException(
                status_code=500,
                detail={"error": "Internal Server Error", "details": str(e)},
            )
    
    
    @app.post(
        "/api/v1/mos_parking/sync",
        responses={
            200: {"description": "Synchronization completed successfully"},
            500: {"model": ErrorResponse, "description": "Internal server error"},
        },
        tags=["admin"],
        summary="Force parking data synchronization",
    )
    async def sync_parking_data() -> dict[str, str]:
        """Forces synchronization of parking data from external source."""
        try:
            use_cases = get_use_cases()
            await use_cases.save_or_update_parking_spots()
            
            logger.info("Parking data synchronization completed via API")
            return {
                "status": "success", 
                "message": "Parking data synchronization completed successfully"
            }
            
        except Exception as e:
            logger.error("Error during parking data synchronization", error=str(e))
            raise HTTPException(
                status_code=500,
                detail={"error": "Internal Server Error", "details": str(e)},
            )
    
    @app.get("/health", tags=["health"])
    async def health_check() -> dict[str, str]:
        """Service health check."""
        return {"status": "healthy"}
