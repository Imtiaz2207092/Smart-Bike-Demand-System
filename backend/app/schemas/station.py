from pydantic import BaseModel


class StationResponse(BaseModel):
    station_id: str
    station_name: str
    latitude: float
    longitude: float
    capacity: int
    station_type: str | None = None

    class Config:
        from_attributes = True