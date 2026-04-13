import json
from dataclasses import dataclass
from datetime import date
from typing import Any

from app.services import geocoding_service
from app.services.weather_service import fetch_current_weather, fetch_forecast_range
from app.utils.parsers import parse_coordinates, parse_iso_date
from app.utils.validators import (
    validate_coordinate_pair,
    validate_date_range_for_forecast,
)


@dataclass
class QueryResult:
    original_location_input: str
    normalized_location: dict[str, Any]
    query_type: str
    start_date: Any
    end_date: Any
    weather: dict[str, Any]
    raw_location_json: str
    raw_weather_json: str


def _manual_coord_json(lat: float, lon: float) -> str:
    return json.dumps(
        {
            "source": "coordinates",
            "latitude": lat,
            "longitude": lon,
        }
    )


def run_weather_query(body: dict, today: date | None = None) -> QueryResult:
    today = today or date.today()
    location_input = (body.get("location_input") or "").strip()
    use_current = bool(body.get("use_current_location"))
    lat_in = body.get("latitude")
    lon_in = body.get("longitude")

    start_raw = body.get("start_date")
    end_raw = body.get("end_date")
    start_date = parse_iso_date(start_raw) if start_raw not in (None, "") else None
    end_date = parse_iso_date(end_raw) if end_raw not in (None, "") else None
    if (start_raw not in (None, "") and start_date is None) or (
        end_raw not in (None, "") and end_date is None
    ):
        raise ValueError("INVALID_DATE_FORMAT")

    if use_current:
        pair = validate_coordinate_pair(lat_in, lon_in)
        if not pair:
            raise ValueError("INVALID_COORDS")
        lat_f, lon_f = pair
        original = location_input or f"{lat_f}, {lon_f}"
        normalized = {
            "name": f"{lat_f:.4f}, {lon_f:.4f}",
            "latitude": lat_f,
            "longitude": lon_f,
            "country": None,
            "region": None,
        }
        raw_location_json = _manual_coord_json(lat_f, lon_f)
    else:
        if not location_input:
            raise ValueError("EMPTY_LOCATION")
        coord = parse_coordinates(location_input)
        if coord:
            lat_f, lon_f = coord
            normalized = {
                "name": f"{lat_f:.4f}, {lon_f:.4f}",
                "latitude": lat_f,
                "longitude": lon_f,
                "country": None,
                "region": None,
            }
            raw_location_json = _manual_coord_json(lat_f, lon_f)
            original = location_input
        else:
            try:
                normalized, raw_text = geocoding_service.resolve_from_text(
                    location_input
                )
            except ValueError as exc:
                code = str(exc)
                raise ValueError(code) from exc
            raw_location_json = json.dumps(
                {"normalized": normalized, "raw_geocode": json.loads(raw_text)}
            )
            lat_f, lon_f = normalized["latitude"], normalized["longitude"]
            original = location_input

    if start_date is None and end_date is None:
        query_type = "current"
        weather, raw_weather_json = fetch_current_weather(lat_f, lon_f)
        start_out = None
        end_out = None
    elif start_date is not None and end_date is not None:
        query_type = "forecast"
        try:
            validate_date_range_for_forecast(start_date, end_date, today)
        except ValueError as exc:
            raise ValueError(str(exc)) from exc
        weather, raw_weather_json = fetch_forecast_range(
            lat_f, lon_f, start_date, end_date
        )
        start_out = start_date
        end_out = end_date
    else:
        raise ValueError("INCOMPLETE_DATE_RANGE")

    return QueryResult(
        original_location_input=original,
        normalized_location=normalized,
        query_type=query_type,
        start_date=start_out,
        end_date=end_out,
        weather=weather,
        raw_location_json=raw_location_json,
        raw_weather_json=raw_weather_json,
    )


def error_message_for_code(code: str) -> tuple[str, str]:
    mapping = {
        "INVALID_COORDS": (
            "Provide valid latitude and longitude with use_current_location.",
            "INVALID_LOCATION_INPUT",
        ),
        "EMPTY_LOCATION": (
            "Location input cannot be empty unless you share your coordinates.",
            "INVALID_LOCATION_INPUT",
        ),
        "LOCATION_NOT_FOUND": (
            "No location matched that search.",
            "LOCATION_NOT_FOUND",
        ),
        "AMBIGUOUS_LOCATION": (
            "That name matches more than one distinct place. Try adding a region or country.",
            "AMBIGUOUS_LOCATION",
        ),
        "INCOMPLETE_DATE_RANGE": (
            "Provide both start_date and end_date, or omit both for current weather.",
            "INVALID_DATE_RANGE",
        ),
        "INVALID_DATE_FORMAT": (
            "start_date and end_date must be valid YYYY-MM-DD values.",
            "INVALID_DATE_RANGE",
        ),
    }
    return mapping.get(code, ("Unable to complete weather query.", "EXTERNAL_API_ERROR"))
