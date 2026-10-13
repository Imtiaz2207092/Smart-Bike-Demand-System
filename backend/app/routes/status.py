
from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session

from app.database import get_db
from app.models import Station, StationSnapshot

router = APIRouter(
    prefix="/stations",
    tags=["Station Status"]
)

SHORTAGE_THRESHOLD = 0.20
SURPLUS_THRESHOLD = 0.80


@router.get("/status")
def get_station_status(db: Session = Depends(get_db)):
    stations = db.query(Station).all()

    results = []

    for station in stations:
        # Get the most recent snapshot for this station
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

        # No recorded data yet
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
                "status": "no_data"
            })
            continue

        bikes = snapshot.available_bikes
        docks = snapshot.available_docks
        percentage = round((bikes / station.capacity) * 100, 2)

        if bikes <= station.capacity * SHORTAGE_THRESHOLD:
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
            "available_docks": docks,
            "bike_percentage": percentage,
            "status": status
        })

    return results
