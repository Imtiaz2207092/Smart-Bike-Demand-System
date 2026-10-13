from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from app.database import Base, engine
from app.models import Station, StationSnapshot
from app.routes.stations import router as station_router
from app.routes.snapshots import router as snapshot_router
from app.routes.status import router as status_router


Base.metadata.create_all(bind=engine)


app = FastAPI(title="Smart Bicycle Demand Forecasting & Redistribution System", version="0.1.0")
app.add_middleware(
    CORSMiddleware,
    allow_origins=[
        "http://localhost:5173",
        "http://127.0.0.1:5173",
    ],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


app.include_router(status_router)
app.include_router(station_router)
app.include_router(snapshot_router)


@app.get("/")
def root():
    return {
        "message": "Smart Bicycle Backend API",
        "status": "running"
    }