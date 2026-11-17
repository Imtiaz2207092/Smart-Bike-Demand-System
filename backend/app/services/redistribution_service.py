from math import radians, sin, cos, asin, sqrt
from typing import Any

TARGET_BIKE_PERCENTAGE = 50


def calculate_distance_km(
    lat1: float,
    lon1: float,
    lat2: float,
    lon2: float,
) -> float:
    """Calculate straight-line distance between two stations."""
    lat1, lon1, lat2, lon2 = map(
        radians, [lat1, lon1, lat2, lon2]
    )

    dlat = lat2 - lat1
    dlon = lon2 - lon1

    a = (
        sin(dlat / 2) ** 2
        + cos(lat1) * cos(lat2) * sin(dlon / 2) ** 2
    )

    return 6371 * 2 * asin(sqrt(min(1.0, a)))


def recommend_redistribution(
    stations: list[dict[str, Any]],
) -> dict[str, Any]:
    """
    Generate suggested transfers from normalized GBFS station data.

    Does not modify station inventory or persist transfers.
    """
    donors = []
    recipients = []
    skipped_stations = []

    for station in stations:
        station_id = station.get("station_id")
        capacity = station.get("capacity")
        bikes = station.get("available_bikes")
        latitude = station.get("latitude")
        longitude = station.get("longitude")

        if (
            not isinstance(capacity, (int, float))
            or isinstance(capacity, bool)
            or capacity <= 0
            or not isinstance(bikes, (int, float))
            or isinstance(bikes, bool)
            or not 0 <= bikes <= capacity
            or not isinstance(latitude, (int, float))
            or not isinstance(longitude, (int, float))
        ):
            skipped_stations.append(station_id)
            continue

        # Ignore stations that are not operational.
        if station.get("station_status") not in (
            None, "operational"
        ):
            skipped_stations.append(station_id)
            continue

        percentage = bikes / capacity * 100
        target = round(
            capacity * TARGET_BIKE_PERCENTAGE / 100
        )

        normalized = {
            "station_id": station_id,
            "station_name": station.get(
                "station_name", f"Station {station_id}"
            ),
            "latitude": latitude,
            "longitude": longitude,
        }

        if percentage >= 80:
            transferable = max(0, int(bikes) - target)
            if transferable:
                donors.append({
                    **normalized,
                    "remaining": transferable,
                })

        elif percentage <= 20:
            needed = min(
                max(0, target - int(bikes)),
                int(capacity - bikes),
            )
            if needed:
                recipients.append({
                    **normalized,
                    "remaining": needed,
                })

    recommendations = []

    # Repeatedly select the nearest available donor-recipient pair.
    while donors and recipients:
        best = min(
            (
                calculate_distance_km(
                    d["latitude"], d["longitude"],
                    r["latitude"], r["longitude"],
                ),
                d,
                r,
            )
            for d in donors
            for r in recipients
        )

        distance, donor, recipient = best
        quantity = min(
            donor["remaining"], recipient["remaining"]
        )

        recommendations.append({
            "from_station_id": donor["station_id"],
            "from_station_name": donor["station_name"],
            "to_station_id": recipient["station_id"],
            "to_station_name": recipient["station_name"],
            "bikes_to_transfer": quantity,
            "distance_km": round(distance, 2),
        })

        donor["remaining"] -= quantity
        recipient["remaining"] -= quantity

        if donor["remaining"] == 0:
            donors.remove(donor)
        if recipient["remaining"] == 0:
            recipients.remove(recipient)

    return {
        "recommendations": recommendations,
        "total_bikes_to_transfer": sum(
            item["bikes_to_transfer"]
            for item in recommendations
        ),
        "unmatched_surplus_stations": [
            {
                "station_id": d["station_id"],
                "remaining_bikes": d["remaining"],
            }
            for d in donors
        ],
        "unmatched_shortage_stations": [
            {
                "station_id": r["station_id"],
                "remaining_bikes_needed": r["remaining"],
            }
            for r in recipients
        ],
        "skipped_station_ids": skipped_stations,
    }
