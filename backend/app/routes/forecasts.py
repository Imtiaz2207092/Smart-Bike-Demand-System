from datetime import datetime

from fastapi import APIRouter, HTTPException
from pydantic import BaseModel, Field

from app.services.demand_service import predict_demand

router = APIRouter(prefix="/api/forecast", tags=["Forecasting"])


class ForecastRequest(BaseModel):
    datetime: datetime
    season: int = Field(ge=1, le=4)
    holiday: int = Field(ge=0, le=1)
    workingday: int = Field(ge=0, le=1)
    weather: int = Field(ge=1, le=4)
    temp: float
    atemp: float
    humidity: float = Field(ge=0, le=100)
    windspeed: float = Field(ge=0)


@router.post("")
def create_forecast(payload: ForecastRequest):
    try:
        return predict_demand(payload.model_dump())
    except ValueError as exc:
        raise HTTPException(status_code=422, detail=str(exc)) from exc
    except FileNotFoundError as exc:
        raise HTTPException(
            status_code=503,
            detail="The trained forecasting model is unavailable.",
        ) from exc
