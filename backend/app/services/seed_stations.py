from app.database import SessionLocal
from app.models.stations import Station


STATIONS = [
    {
        "station_id": "ST-101",
        "station_name": "KUET Campus",
        "latitude": 23.7771,
        "longitude": 90.3801,
        "capacity": 50,
        "station_type": "education",
    },
    {
        "station_id": "ST-102",
        "station_name": "Fulbari Gate",
        "latitude": 23.7925,
        "longitude": 90.4078,
        "capacity": 40,
        "station_type": "commuter",
    },
    {
        "station_id": "ST-103",
        "station_name": "Daulatpur",
        "latitude": 23.7805,
        "longitude": 90.4167,
        "capacity": 60,
        "station_type": "commuter",
    },
    {
        "station_id": "ST-104",
        "station_name": "Dakbanglo",
        "latitude": 23.8103,
        "longitude": 90.4125,
        "capacity": 45,
        "station_type": "commuter",
    },
    {
        "station_id": "ST-105",
        "station_name": "Khulna University Campus",
        "latitude": 23.7532,
        "longitude": 90.3751,
        "capacity": 35,
        "station_type": "education",
    },
    {
        "station_id": "ST-106",
        "station_name": "Sonadanga Residential Area",
        "latitude": 23.8221,
        "longitude": 90.3654,
        "capacity": 30,
        "station_type": "residential",
    },
    {
        "station_id": "ST-107",
        "station_name": "Zero Point",
        "latitude": 23.7650,
        "longitude": 90.3890,
        "capacity": 50,
        "station_type": "commercial",
    },
    {
        "station_id": "ST-108",
        "station_name": "Boyra",
        "latitude": 23.8350,
        "longitude": 90.4210,
        "capacity": 35,
        "station_type": "residential",
    },
    {
        "station_id": "ST-109",
        "station_name": "Fultola",
        "latitude": 23.7410,
        "longitude": 90.3950,
        "capacity": 30,
        "station_type": "commercial",
    },
    {
        "station_id": "ST-110",
        "station_name": "Sports Stadium",
        "latitude": 23.8050,
        "longitude": 90.3680,
        "capacity": 40,
        "station_type": "recreational",
    },
]



def seed_stations():
    db = SessionLocal()

    try:
        inserted = 0
        updated = 0

        for station_data in STATIONS:
            existing = (
                db.query(Station)
                .filter_by(station_id=station_data["station_id"])
                .first()
            )

            if existing is None:
                db.add(Station(**station_data))
                inserted += 1
            else:
                for key, value in station_data.items():
                    setattr(existing, key, value)
                updated += 1

        db.commit()
        print(
            f"Successfully inserted {inserted} new stations "
            f"and updated {updated} existing stations."
        )

    except Exception:
        db.rollback()
        raise

    finally:
        db.close()


if __name__ == "__main__":
    seed_stations()