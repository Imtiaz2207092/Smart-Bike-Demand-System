from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session

from app.database import get_db
from app.models import Station, StationSnapshot
from app.schemas.snapshot import SnapshotCreate, SnapshotResponse

router = APIRouter(prefix="/snapshots", tags=["Snapshots"])


@router.post("/", response_model=SnapshotResponse, status_code=201)
def create_snapshot(
    snapshot: SnapshotCreate,
    db: Session = Depends(get_db)
):
    station = db.query(Station).filter(
        Station.station_id == snapshot.station_id
    ).first()

    if station is None:
        raise HTTPException(
            status_code=404,
            detail="Station not found"
        )

    if snapshot.available_bikes + snapshot.available_docks > station.capacity:
        raise HTTPException(
            status_code=400,
            detail="Available bikes and docks exceed station capacity"
        )

    db_snapshot = StationSnapshot(
        station_id=snapshot.station_id,
        available_bikes=snapshot.available_bikes,
        available_docks=snapshot.available_docks
    )

    db.add(db_snapshot)
    db.commit()
    db.refresh(db_snapshot)

    return db_snapshot


@router.get("/", response_model=list[SnapshotResponse])
def get_snapshots(db: Session = Depends(get_db)):
    return (
        db.query(StationSnapshot)
        .order_by(StationSnapshot.recorded_at.desc())
        .all()
    )