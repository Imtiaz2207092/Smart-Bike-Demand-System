from app.services.gbfs_service import normalize_station_snapshot


def test_normalize_station_snapshot_uses_official_gbfs_fields():
    info = {
        "station_id": "abc-123",
        "name": "Test Station",
        "lat": 38.9,
        "lon": -77.0,
        "capacity": 20,
        "is_charging": False,
    }
    status = {
        "station_id": "abc-123",
        "num_bikes_available": 11,
        "num_ebikes_available": 2,
        "num_docks_available": 9,
        "is_installed": 1,
        "is_renting": 1,
        "is_returning": 1,
        "last_reported": 1700000000,
    }

    snapshot = normalize_station_snapshot(info, status)

    assert snapshot["station_id"] == "abc-123"
    assert snapshot["station_name"] == "Test Station"
    assert snapshot["available_bikes"] == 11
    assert snapshot["available_e_bikes"] == 2
    assert snapshot["available_mechanical_bikes"] == 9
    assert snapshot["empty_docks"] == 9
    assert snapshot["capacity"] == 20
    assert snapshot["station_status"] == "operational"
    assert snapshot["source_timestamp"] == 1700000000
    assert snapshot["source"] == "capital_bikeshare_gbfs"
    assert snapshot["is_live"] is True
