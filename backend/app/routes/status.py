from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session

from app.database import get_db
from app.models import Station, StationSnapshot
from app.services.gbfs_service import gbfs_service

router = APIRouter(
    prefix="/stations",
    tags=["Station Status"]
)

SHORTAGE_THRESHOLD = 0.20
SURPLUS_THRESHOLD = 0.80


def _build_station_status_payload(source_station: dict, live_snapshot: dict | None):
    capacity = source_station.get("capacity")
    available_bikes = source_station.get("available_bikes")
    if available_bikes is not None and capacity is not None and capacity > 0:
        percentage = round((available_bikes / capacity) * 100, 2)
    else:
        percentage = None

    if available_bikes is None or capacity in (None, 0):
        status = "no_data"
    elif available_bikes <= capacity * SHORTAGE_THRESHOLD:
        status = "shortage"
    elif available_bikes >= capacity * SURPLUS_THRESHOLD:
        status = "surplus"
    else:
        status = "balanced"

    return {
        "station_id": source_station.get("station_id"),
        "station_name": source_station.get("station_name"),
        "latitude": source_station.get("latitude"),
        "longitude": source_station.get("longitude"),
        "capacity": capacity,
        "available_bikes": available_bikes,
        "available_e_bikes": source_station.get("available_e_bikes"),
        "available_mechanical_bikes": source_station.get("available_mechanical_bikes"),
        "available_docks": source_station.get("available_docks"),
        "empty_docks": source_station.get("empty_docks"),
        "bike_percentage": percentage,
        "status": status,
        "station_status": source_station.get("station_status"),
        "source": source_station.get("source", "capital_bikeshare_gbfs"),
        "is_live": source_station.get("is_live", True),
        "source_timestamp": source_station.get("source_timestamp"),
        "last_station_status_update_time": source_station.get("last_station_status_update_time"),
        "last_successful_fetch": live_snapshot.get("last_successful_fetch") if live_snapshot else None,
        "fetch_status": live_snapshot.get("fetch_status") if live_snapshot else "unavailable",
        "stale": live_snapshot.get("stale", True) if live_snapshot else True,
    }


@router.get("/status")
def get_station_status(db: Session = Depends(get_db)):
    live_snapshot = gbfs_service.fetch_latest()
    stations = live_snapshot.get("stations", [])

    if not stations:
        local_stations = db.query(Station).all()
        results = []
        for station in local_stations:
            snapshot = (
                db.query(StationSnapshot)
                .filter(
                    StationSnapshot.station_id == station.station_id
                )
                .order_by(
                    StationSnapshot.recorded_at.desc(),
                    StationSnapshot.id.desc()
                )
                .first()
            )

            if snapshot is None:
                results.append({
                    "station_id": station.station_id,
                    "station_name": station.station_name,
                    "latitude": station.latitude,
                    "longitude": station.longitude,
                    "capacity": station.capacity,
                    "available_bikes": None,
                    "available_docks": None,
                    "bike_percentage": None,
                    "status": "no_data",
                    "station_status": "unknown",
                    "source": "local_station_metadata",
                    "is_live": False,
                    "source_timestamp": None,
                    "last_station_status_update_time": None,
                    "last_successful_fetch": live_snapshot.get("last_successful_fetch"),
                    "fetch_status": live_snapshot.get("fetch_status", "unavailable"),
                    "stale": live_snapshot.get("stale", True),
                })
                continue

            bikes = snapshot.available_bikes
            docks = snapshot.available_docks
            percentage = round((bikes / station.capacity) * 100, 2) if station.capacity else None

            if bikes is None or station.capacity in (None, 0):
                status = "no_data"
            elif bikes <= station.capacity * SHORTAGE_THRESHOLD:
                status = "shortage"
            elif bikes >= station.capacity * SURPLUS_THRESHOLD:
                status = "surplus"
            else:
                status = "balanced"

            results.append({
                "station_id": station.station_id,
                "station_name": station.station_name,
                "latitude": station.latitude,
                "longitude": station.longitude,
                "capacity": station.capacity,
                "available_bikes": bikes,
                "available_e_bikes": None,
                "available_mechanical_bikes": None,
                "available_docks": docks,
                "empty_docks": docks,
                "bike_percentage": percentage,
                "status": status,
                "station_status": "unknown",
                "source": "local_station_metadata",
                "is_live": False,
                "source_timestamp": None,
                "last_station_status_update_time": None,
                "last_successful_fetch": live_snapshot.get("last_successful_fetch"),
                "fetch_status": live_snapshot.get("fetch_status", "unavailable"),
                "stale": live_snapshot.get("stale", True),
            })
        return results

    return [_build_station_status_payload(station, live_snapshot) for station in stations]


@router.get("/live")
def get_live_stations():
    live_snapshot = gbfs_service.fetch_latest()
    stations = [
        _build_station_status_payload(station, live_snapshot)
        for station in live_snapshot.get("stations", [])
    ]
    return {
        "stations": stations,
        "fetch_status": live_snapshot.get("fetch_status", "unavailable"),
        "last_successful_fetch": live_snapshot.get("last_successful_fetch"),
        "last_source_timestamp": live_snapshot.get("last_source_timestamp"),
        "stale": live_snapshot.get("stale", True),
        "source": live_snapshot.get("source", "capital_bikeshare_gbfs"),
        "status": "ok" if live_snapshot.get("fetch_status") == "ok" else "unavailable",
    }


@router.get("/live/{station_id}")
def get_live_station(station_id: str):
    live_snapshot = gbfs_service.fetch_latest()
    for station in live_snapshot.get("stations", []):
        if station.get("station_id") == station_id:
            return _build_station_status_payload(station, live_snapshot)
    raise HTTPException(status_code=404, detail="Station not found in the latest GBFS snapshot")


@router.get("/live/summary")
def get_live_station_summary():
    live_snapshot = gbfs_service.fetch_latest()
    stations = live_snapshot.get("stations", [])
    if not stations:
        return {
            "total_stations": 0,
            "total_available_bikes": 0,
            "fetch_status": live_snapshot.get("fetch_status", "unavailable"),
            "last_successful_fetch": live_snapshot.get("last_successful_fetch"),
            "stale": live_snapshot.get("stale", True),
        }

    return {
        "total_stations": len(stations),
        "total_available_bikes": sum(
            int(station.get("available_bikes") or 0)
            for station in stations
            if station.get("available_bikes") is not None
        ),
        "fetch_status": live_snapshot.get("fetch_status", "unavailable"),
        "last_successful_fetch": live_snapshot.get("last_successful_fetch"),
        "last_source_timestamp": live_snapshot.get("last_source_timestamp"),
        "stale": live_snapshot.get("stale", True),
    }
