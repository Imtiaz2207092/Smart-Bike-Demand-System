from fastapi import APIRouter, HTTPException

from app.services.gbfs_service import gbfs_service
from app.services.redistribution_service import recommend_redistribution

router = APIRouter(
    prefix="/api/redistribution",
    tags=["Redistribution"],
)


@router.get("")
def get_redistribution_recommendations():
    """Generate redistribution recommendations from the latest GBFS station data."""
    try:
        latest_data = gbfs_service.fetch_latest()

        if not isinstance(latest_data, dict):
            raise HTTPException(
                status_code=503,
                detail="Station data is currently unavailable.",
            )

        stations = latest_data.get("stations", [])

        if not stations:
            return {
                "status": "no_data",
                "message": "No station data is available for redistribution.",
                "source": latest_data.get("source"),
                "stale": latest_data.get("stale", False),
                "recommendations": [],
                "total_bikes_to_transfer": 0,
                "unmatched_surplus_stations": [],
                "unmatched_shortage_stations": [],
                "skipped_station_ids": [],
            }

        result = recommend_redistribution(stations)

        return {
            "status": "success",
            "message": "Redistribution recommendations generated.",
            "source": latest_data.get("source"),
            "fetch_status": latest_data.get("fetch_status"),
            "stale": latest_data.get("stale", False),
            "last_successful_fetch": latest_data.get("last_successful_fetch"),
            "station_count": len(stations),
            **result,
        }

    except HTTPException:
        raise
    except Exception as exc:
        raise HTTPException(
            status_code=500,
            detail=f"Failed to generate redistribution recommendations: {exc}",
        ) from exc
