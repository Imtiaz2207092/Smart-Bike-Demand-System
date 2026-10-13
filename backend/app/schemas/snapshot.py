from datetime import datetime

from pydantic import BaseModel, Field, ConfigDict


class SnapshotCreate(BaseModel):
    station_id: str
    available_bikes: int = Field(ge=0)
    available_docks: int = Field(ge=0)


class SnapshotResponse(BaseModel):
    id: int
    station_id: str
    available_bikes: int
    available_docks: int
    recorded_at: datetime

    model_config = ConfigDict(from_attributes=True)