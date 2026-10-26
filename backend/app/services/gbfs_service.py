from __future__ import annotations

import json
from datetime import datetime, timezone
from threading import Lock
from typing import Any
from urllib.error import HTTPError, URLError
from urllib.request import Request, urlopen

DISCOVERY_URL = "https://gbfs.capitalbikeshare.com/gbfs/2.3/gbfs.json"
REQUEST_TIMEOUT_SECONDS = 20


class GBFSService:
    def __init__(self) -> None:
        self._lock = Lock()
        self.last_successful_fetch: datetime | None = None
        self.last_snapshot: dict[str, Any] = {
            "stations": [],
            "fetch_status": "unavailable",
            "stale": True,
            "last_successful_fetch": None,
            "last_source_timestamp": None,
            "source": "capital_bikeshare_gbfs",
        }
        self.last_error: str | None = None

    def fetch_latest(self) -> dict[str, Any]:
        with self._lock:
            try:
                feed_urls = self._discover_feed_urls()
                info = self._fetch_json(feed_urls["station_information"])
                status = self._fetch_json(feed_urls["station_status"])

                station_info = info.get("data", {}).get("stations", [])
                station_status = status.get("data", {}).get("stations", [])

                merged_stations = []
                for station in self._merge_station_records(station_info, station_status):
                    if station is not None:
                        merged_stations.append(station)

                source_timestamp = max(
                    [station.get("source_timestamp") for station in merged_stations if station.get("source_timestamp") is not None],
                    default=None,
                )
                fetch_timestamp = datetime.now(timezone.utc)
                self.last_successful_fetch = fetch_timestamp
                self.last_error = None
                self.last_snapshot = {
                    "stations": merged_stations,
                    "fetch_status": "ok",
                    "stale": False,
                    "last_successful_fetch": fetch_timestamp.isoformat(),
                    "last_source_timestamp": source_timestamp,
                    "source": "capital_bikeshare_gbfs",
                }
                return self.last_snapshot
            except Exception as exc:  # pragma: no cover - runtime guard
                self.last_error = str(exc)
                snapshot = dict(self.last_snapshot)
                snapshot["fetch_status"] = "error"
                snapshot["stale"] = True
                snapshot["last_successful_fetch"] = (
                    self.last_successful_fetch.isoformat() if self.last_successful_fetch else None
                )
                snapshot["source"] = "capital_bikeshare_gbfs"
                return snapshot

    def _discover_feed_urls(self) -> dict[str, str]:
        discovery = self._fetch_json(DISCOVERY_URL)
        payload = discovery.get("data", {})
        if not payload:
            raise ValueError("No GBFS discovery data was returned.")

        language_payload = None
        for entry in payload.values():
            feeds = entry.get("feeds", [])
            if feeds:
                language_payload = entry
                break
        if language_payload is None:
            raise ValueError("No GBFS language feed list was found in the root discovery document.")

        feed_map = {feed.get("name"): feed.get("url") for feed in language_payload.get("feeds", []) if feed.get("name") and feed.get("url")}
        required_names = {"station_information", "station_status"}
        missing = sorted(required_names.difference(feed_map.keys()))
        if missing:
            raise ValueError(f"Missing required GBFS feed(s): {', '.join(missing)}")

        return {
            "station_information": feed_map["station_information"],
            "station_status": feed_map["station_status"],
        }

    def _merge_station_records(self, station_info_records: list[dict[str, Any]], station_status_records: list[dict[str, Any]]) -> list[dict[str, Any]]:
        info_by_id = {
            record.get("station_id"): record
            for record in station_info_records
            if isinstance(record, dict) and record.get("station_id") is not None
        }
        status_by_id = {
            record.get("station_id"): record
            for record in station_status_records
            if isinstance(record, dict) and record.get("station_id") is not None
        }

        merged = []
        for station_id in sorted(set(info_by_id) | set(status_by_id)):
            info_record = info_by_id.get(station_id)
            status_record = status_by_id.get(station_id)
            normalized = normalize_station_snapshot(info_record, status_record)
            if normalized is not None:
                merged.append(normalized)
        return merged

    def _fetch_json(self, url: str) -> dict[str, Any]:
        request = Request(url, headers={"User-Agent": "SmartBikeDemandSystem/1.0"})
        with urlopen(request, timeout=REQUEST_TIMEOUT_SECONDS) as response:
            raw = response.read()
            return json.loads(raw.decode("utf-8"))


def _coerce_int(value: Any) -> int | None:
    if value is None:
        return None
    if isinstance(value, bool):
        return int(value)
    if isinstance(value, (int, float)):
        if isinstance(value, float) and value.is_integer():
            return int(value)
        return int(value)
    if isinstance(value, str):
        stripped = value.strip()
        if not stripped:
            return None
        try:
            return int(float(stripped))
        except ValueError:
            return None
    return None


def _compute_status_label(available_bikes: int | None, capacity: int | None) -> str:
    if available_bikes is None or capacity is None or capacity <= 0:
        return "no_data"
    threshold_low = capacity * 0.20
    threshold_high = capacity * 0.80
    if available_bikes <= threshold_low:
        return "shortage"
    if available_bikes >= threshold_high:
        return "surplus"
    return "balanced"


def _resolve_station_operational_status(status_data: dict[str, Any] | None) -> str:
    if not status_data:
        return "unknown"
    if status_data.get("is_installed") in (0, False):
        return "out_of_service"
    if status_data.get("is_renting") in (0, False):
        return "not_renting"
    if status_data.get("is_returning") in (0, False):
        return "not_returning"
    return "operational"


def normalize_station_snapshot(info: dict[str, Any] | None, status: dict[str, Any] | None) -> dict[str, Any] | None:
    if info is None and status is None:
        return None

    station_id = (info or {}).get("station_id") or (status or {}).get("station_id")
    if station_id is None:
        return None

    available_bikes = _coerce_int((status or {}).get("num_bikes_available"))
    available_e_bikes = _coerce_int((status or {}).get("num_ebikes_available"))
    available_docks = _coerce_int((status or {}).get("num_docks_available"))
    capacity = _coerce_int((info or {}).get("capacity"))
    source_timestamp = _coerce_int((status or {}).get("last_reported"))

    mechanical_bikes = None
    if available_bikes is not None and available_e_bikes is not None and available_bikes >= available_e_bikes:
        mechanical_bikes = available_bikes - available_e_bikes

    station_name = (info or {}).get("name") or (status or {}).get("name") or f"Station {station_id}"
    latitude = (info or {}).get("lat") or (status or {}).get("lat")
    longitude = (info or {}).get("lon") or (status or {}).get("lon")

    return {
        "station_id": station_id,
        "station_name": station_name,
        "latitude": latitude,
        "longitude": longitude,
        "capacity": capacity,
        "available_bikes": available_bikes,
        "available_e_bikes": available_e_bikes,
        "available_mechanical_bikes": mechanical_bikes,
        "available_docks": available_docks,
        "empty_docks": available_docks,
        "source_timestamp": source_timestamp,
        "last_station_status_update_time": source_timestamp,
        "station_status": _resolve_station_operational_status(status),
        "status": _compute_status_label(available_bikes, capacity),
        "bike_percentage": round((available_bikes / capacity) * 100, 2) if available_bikes is not None and capacity and capacity > 0 else None,
        "source": "capital_bikeshare_gbfs",
        "is_live": True,
    }


gbfs_service = GBFSService()
