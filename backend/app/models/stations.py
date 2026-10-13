from sqlalchemy import Column, String, Float, Integer

from app.database import Base


class Station(Base):
    __tablename__ = "stations"

    station_id = Column(String, primary_key=True)
    station_name = Column(String, nullable=False)
    latitude = Column(Float, nullable=False)
    longitude = Column(Float, nullable=False)
    capacity = Column(Integer, nullable=False)
    station_type = Column(String, nullable=True)