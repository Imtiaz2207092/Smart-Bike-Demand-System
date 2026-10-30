from math import radians, sin, cos, asin, sqrt
from typing import Any

from app.services.redistribution_service import calculate_distance_km


NORMAL_TARGET_PERCENTAGE = 50
PEAK_TARGET_PERCENTAGE = 60

DONOR_THRESHOLD_PERCENTAGE = 80
RECIPIENT_THRESHOLD_PERCENTAGE = 20


def recommend_forecast_redistribution(
    stations: list[dict[str, Any]],
    is_peak_hour: int,
) -> dict[str, Any]:
    """
    Generate forecast-informed transfer suggestions.

    The model supplies a system-wide peak-hour signal, not
    station-specific demand predictions. Transfers are suggestions
    only; station inventory is not modified.
    """
    target_percentage = (
        PEAK_TARGET_PERCENTAGE
        if is_peak_hour == 1
        else NORMAL_TARGET_PERCENTAGE
    )

    donors = []
    recipients = []
    skipped_station_ids = []

    for station in stations:
        station_id = station.get("station_id")
        capacity = station.get("capacity")
        bikes = station.get("available_bikes")
        latitude = station.get("latitude")
        longitude = station.get("longitude")

        valid_numbers = (
            isinstance(capacity, (int, float))
            and not isinstance(capacity, bool)
            and capacity > 0
            and isinstance(bikes, (int, float))
            and not isinstance(bikes, bool)
            and 0 <= bikes <= capacity
            and isinstance(latitude, (int, float))
            and not isinstance(latitude, bool)
            and isinstance(longitude, (int, float))
            and not isinstance(longitude, bool)
        )

        if not valid_numbers:
            skipped_station_ids.append(station_id)
            continue

        if station.get("station_status") not in (
            None, "operational"
        ):
            skipped_station_ids.append(station_id)
            continue

        bike_percentage = bikes / capacity * 100
        target_bikes = round(capacity * target_percentage / 100)

        normalized = {
            "station_id": station_id,
            "station_name": station.get(
                "station_name", f"Station {station_id}"
            ),
            "latitude": latitude,
            "longitude": longitude,
        }

        if bike_percentage >= DONOR_THRESHOLD_PERCENTAGE:
            surplus = max(0, int(bikes) - target_bikes)
            if surplus > 0:
                donors.append({
                    **normalized,
                    "remaining": surplus,
                })

        elif bike_percentage <= RECIPIENT_THRESHOLD_PERCENTAGE:
            needed = min(
                max(0, target_bikes - int(bikes)),
                int(capacity - bikes),
            )
            if needed > 0:
                recipients.append({
                    **normalized,
                    "remaining": needed,
                })

    recommendations = []

    while donors and recipients:
        candidates = [
            (
                calculate_distance_km(
                    donor["latitude"],
                    donor["longitude"],
                    recipient["latitude"],
                    recipient["longitude"],
                ),
                donor,
                recipient,
            )
            for donor in donors
            for recipient in recipients
        ]

        distance, donor, recipient = min(
            candidates, key=lambda item: item[0]
        )

        quantity = min(
            donor["remaining"],
            recipient["remaining"],
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
        "target_bike_percentage": target_percentage,
        "thresholds": {
            "donor_at_or_above_percentage":
                DONOR_THRESHOLD_PERCENTAGE,
            "recipient_at_or_below_percentage":
                RECIPIENT_THRESHOLD_PERCENTAGE,
        },
        "recommendations": recommendations,
        "total_bikes_to_transfer": sum(
            item["bikes_to_transfer"]
            for item in recommendations
        ),
        "unmatched_surplus_stations": [
            {
                "station_id": donor["station_id"],
                "remaining_bikes": donor["remaining"],
            }
            for donor in donors
        ],
        "unmatched_shortage_stations": [
            {
                "station_id": recipient["station_id"],
                "remaining_bikes_needed": recipient["remaining"],
            }
            for recipient in recipients
        ],
        "skipped_station_ids": skipped_station_ids,
    }
