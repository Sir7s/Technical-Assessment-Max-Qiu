from datetime import datetime
from unittest.mock import patch

from app.extensions import db
from app.models.weather_record import WeatherRecord


def _seed_record(app):
    with app.app_context():
        r = WeatherRecord(
            original_location_input="Seed",
            resolved_location_name="Seed City",
            latitude=1.0,
            longitude=2.0,
            country="S",
            region=None,
            query_type="current",
            weather_summary="Clear",
            temperature_c=20.0,
            raw_weather_json="{}",
            raw_location_json="{}",
            created_at=datetime.utcnow(),
            updated_at=datetime.utcnow(),
        )
        db.session.add(r)
        db.session.commit()
        return r.id


def _geo():
    return {
        "results": [
            {
                "name": "Other",
                "latitude": 5.0,
                "longitude": 6.0,
                "country": "S",
                "admin1": None,
            }
        ]
    }


def _wx():
    return {
        "latitude": 5.0,
        "longitude": 6.0,
        "utc_offset_seconds": 0,
        "current": {
            "temperature_2m": 1.0,
            "relative_humidity_2m": 2.0,
            "apparent_temperature": 3.0,
            "weather_code": 0,
            "wind_speed_10m": 4.0,
            "precipitation_probability": 5.0,
            "uv_index": 1.0,
        },
        "hourly": {"time": [], "visibility": []},
        "daily": {
            "time": ["2026-04-13"],
            "sunrise": ["2026-04-13T06:00"],
            "sunset": ["2026-04-13T18:00"],
            "weather_code": [0],
            "uv_index_max": [1.0],
            "precipitation_probability_max": [5.0],
        },
    }


@patch("app.services.geocoding_service.requests.get")
@patch("app.services.weather_service.requests.get")
def test_update_refreshes_record(mock_wx, mock_geo, app, client):
    rid = _seed_record(app)
    mock_geo.return_value.json.return_value = _geo()
    mock_geo.return_value.raise_for_status = lambda: None
    mock_wx.return_value.json.return_value = _wx()
    mock_wx.return_value.raise_for_status = lambda: None

    res = client.put(
        f"/api/records/{rid}",
        json={"location_input": "Other"},
    )
    assert res.status_code == 200
    body = res.get_json()
    assert body["data"]["record"]["resolved_location_name"] == "Other, S"


def test_delete_record(app, client):
    rid = _seed_record(app)
    res = client.delete(f"/api/records/{rid}")
    assert res.status_code == 200
    assert client.get(f"/api/records/{rid}").status_code == 404


def test_get_missing_record(client):
    res = client.get("/api/records/99999")
    assert res.status_code == 404
