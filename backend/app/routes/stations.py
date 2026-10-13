from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session

from app.database import get_db
from app.models.stations import Station
from app.schemas.station import StationResponse


router = APIRouter(
    prefix="/stations",
    tags=["Stations"]
)


@router.get("/", response_model=list[StationResponse])
def get_stations(
    db: Session = Depends(get_db)
):
    return db.query(Station).all()