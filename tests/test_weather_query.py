from datetime import date, timedelta
from unittest.mock import patch


def _geo_response():
    return {
        "results": [
            {
                "name": "Testville",
                "latitude": 10.0,
                "longitude": 20.0,
                "country": "Nowhere",
                "admin1": "Region X",
            }
        ]
    }


def _weather_current():
    return {
        "latitude": 10.0,
        "longitude": 20.0,
        "utc_offset_seconds": 0,
        "current": {
            "temperature_2m": 12.3,
            "relative_humidity_2m": 55.0,
            "apparent_temperature": 11.0,
            "weather_code": 0,
            "wind_speed_10m": 15.0,
            "precipitation_probability": 5.0,
            "uv_index": 3.2,
        },
        "hourly": {"time": ["2026-04-13T12:00"], "visibility": [10000.0]},
        "daily": {
            "time": ["2026-04-13"],
            "sunrise": ["2026-04-13T06:00"],
            "sunset": ["2026-04-13T18:00"],
            "weather_code": [0],
            "uv_index_max": [3.0],
            "precipitation_probability_max": [5.0],
        },
    }


@patch("app.services.geocoding_service.requests.get")
@patch("app.services.weather_service.requests.get")
def test_weather_query_creates_record(mock_wx, mock_geo, client):
    mock_geo.return_value.json.return_value = _geo_response()
    mock_geo.return_value.raise_for_status = lambda: None
    mock_wx.return_value.json.return_value = _weather_current()
    mock_wx.return_value.raise_for_status = lambda: None

    res = client.post(
        "/api/weather/query",
        json={"location_input": "Testville"},
    )
    assert res.status_code == 201
    body = res.get_json()
    assert body["success"] is True
    assert body["data"]["record"]["resolved_location_name"] == "Testville, Region X, Nowhere"
    assert body["data"]["record"]["query_type"] == "current"

    listed = client.get("/api/records").get_json()
    assert len(listed["data"]["records"]) == 1


def test_invalid_location_empty(client):
    res = client.post("/api/weather/query", json={"location_input": "   "})
    assert res.status_code == 400
    assert res.get_json()["success"] is False


@patch("app.services.geocoding_service.requests.get")
def test_location_not_found(mock_geo, client):
    mock_geo.return_value.json.return_value = {"results": []}
    mock_geo.return_value.raise_for_status = lambda: None

    res = client.post(
        "/api/weather/query",
        json={"location_input": "zzzznotacity12345"},
    )
    assert res.status_code == 400
    assert res.get_json()["error"]["code"] == "LOCATION_NOT_FOUND"


def test_incomplete_dates(client):
    res = client.post(
        "/api/weather/query",
        json={"location_input": "10, 20", "start_date": "2026-04-14"},
    )
    assert res.status_code == 400
    assert res.get_json()["error"]["code"] == "INVALID_DATE_RANGE"


@patch("app.services.geocoding_service.requests.get")
@patch("app.services.weather_service.requests.get")
def test_forecast_query(mock_wx, mock_geo, client):
    mock_geo.return_value.json.return_value = _geo_response()
    mock_geo.return_value.raise_for_status = lambda: None
    today = date.today()
    tomorrow = today + timedelta(days=1)
    mock_wx.return_value.json.return_value = {
        "daily": {
            "time": [today.isoformat(), tomorrow.isoformat()],
            "weather_code": [1, 2],
            "temperature_2m_max": [10, 11],
            "temperature_2m_min": [5, 6],
            "apparent_temperature_max": [9, 10],
            "apparent_temperature_min": [4, 5],
            "precipitation_probability_max": [10, 20],
            "uv_index_max": [2, 3],
            "sunrise": [f"{today.isoformat()}T06:00", f"{tomorrow.isoformat()}T06:00"],
            "sunset": [f"{today.isoformat()}T18:00", f"{tomorrow.isoformat()}T18:00"],
            "wind_speed_10m_max": [12, 13],
        }
    }
    mock_wx.return_value.raise_for_status = lambda: None

    start = today.isoformat()
    end = today.isoformat()

    res = client.post(
        "/api/weather/query",
        json={
            "location_input": "Testville",
            "start_date": start,
            "end_date": end,
        },
    )
    assert res.status_code == 201
    assert res.get_json()["data"]["record"]["query_type"] == "forecast"
