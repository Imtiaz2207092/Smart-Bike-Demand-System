from app.services.redistribution_service import recommend_redistribution


stations = [
    {
        "station_id": "ST-101",
        "station_name": "KUET Campus",
        "latitude": 22.9000,
        "longitude": 89.5000,
        "capacity": 50,
        "available_bikes": 5,
    },
    {
        "station_id": "ST-102",
        "station_name": "Fulbari Gate",
        "latitude": 22.9100,
        "longitude": 89.5100,
        "capacity": 50,
        "available_bikes": 45,
    },
    {
        "station_id": "ST-103",
        "station_name": "Daulatpur",
        "latitude": 22.9200,
        "longitude": 89.5200,
        "capacity": 40,
        "available_bikes": 20,
    },
]

result = recommend_redistribution(stations)

print("Redistribution result:")
print(result)

assert result["total_bikes_to_transfer"] == 20
assert len(result["recommendations"]) == 1
assert result["recommendations"][0]["from_station_id"] == "ST-102"
assert result["recommendations"][0]["to_station_id"] == "ST-101"
assert result["recommendations"][0]["bikes_to_transfer"] == 20

print("All basic redistribution tests passed!")
