import csv
import io

from app.models.weather_record import WeatherRecord


CSV_COLUMNS = [
    "id",
    "created_at",
    "updated_at",
    "original_location_input",
    "resolved_location_name",
    "latitude",
    "longitude",
    "country",
    "region",
    "query_type",
    "start_date",
    "end_date",
    "weather_summary",
    "temperature_c",
    "apparent_temperature_c",
    "humidity_percent",
    "wind_speed_kmh",
    "precipitation_probability_percent",
    "visibility_m",
    "uv_index",
    "sunrise",
    "sunset",
]


def records_to_csv_bytes(records: list[WeatherRecord]) -> bytes:
    buf = io.StringIO()
    writer = csv.DictWriter(buf, fieldnames=CSV_COLUMNS, extrasaction="ignore")
    writer.writeheader()
    for r in records:
        writer.writerow(_row_dict(r))
    return buf.getvalue().encode("utf-8-sig")


def _row_dict(r: WeatherRecord) -> dict:
    return {
        "id": r.id,
        "created_at": r.created_at.isoformat() if r.created_at else "",
        "updated_at": r.updated_at.isoformat() if r.updated_at else "",
        "original_location_input": r.original_location_input,
        "resolved_location_name": r.resolved_location_name,
        "latitude": r.latitude,
        "longitude": r.longitude,
        "country": r.country or "",
        "region": r.region or "",
        "query_type": r.query_type,
        "start_date": r.start_date.isoformat() if r.start_date else "",
        "end_date": r.end_date.isoformat() if r.end_date else "",
        "weather_summary": r.weather_summary or "",
        "temperature_c": r.temperature_c if r.temperature_c is not None else "",
        "apparent_temperature_c": (
            r.apparent_temperature_c if r.apparent_temperature_c is not None else ""
        ),
        "humidity_percent": r.humidity_percent if r.humidity_percent is not None else "",
        "wind_speed_kmh": r.wind_speed_kmh if r.wind_speed_kmh is not None else "",
        "precipitation_probability_percent": (
            r.precipitation_probability_percent
            if r.precipitation_probability_percent is not None
            else ""
        ),
        "visibility_m": r.visibility_m if r.visibility_m is not None else "",
        "uv_index": r.uv_index if r.uv_index is not None else "",
        "sunrise": r.sunrise or "",
        "sunset": r.sunset or "",
    }
