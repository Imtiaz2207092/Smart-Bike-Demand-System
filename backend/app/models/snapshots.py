from sqlalchemy import Column, Integer, String, DateTime, ForeignKey
from sqlalchemy.sql import func

from app.database import Base


class StationSnapshot(Base):
    __tablename__ = "station_snapshots"

    id = Column(Integer, primary_key=True, index=True)
    station_id = Column(
        String,
        ForeignKey("stations.station_id"),
        nullable=False,
        index=True
    )
    available_bikes = Column(Integer, nullable=False)
    available_docks = Column(Integer, nullable=False)
    recorded_at = Column(
        DateTime(timezone=True),
        server_default=func.now(),
        nullable=False,
        index=True
    )