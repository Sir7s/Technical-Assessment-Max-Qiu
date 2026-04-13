from datetime import datetime

from app.extensions import db
from app.models.weather_record import WeatherRecord


def _seed(app):
    with app.app_context():
        r = WeatherRecord(
            original_location_input="A",
            resolved_location_name="B",
            latitude=1.0,
            longitude=2.0,
            country=None,
            region=None,
            query_type="current",
            weather_summary="X",
            temperature_c=1.0,
            raw_weather_json="{}",
            raw_location_json="{}",
            created_at=datetime.utcnow(),
            updated_at=datetime.utcnow(),
        )
        db.session.add(r)
        db.session.commit()


def test_csv_export_headers_and_row(app, client):
    _seed(app)
    res = client.get("/api/records/export/csv")
    assert res.status_code == 200
    assert "text/csv" in res.headers["Content-Type"]
    text = res.data.decode("utf-8-sig")
    lines = [ln for ln in text.splitlines() if ln.strip()]
    assert lines[0].startswith("id,")
    assert len(lines) >= 2


def test_csv_empty_still_has_headers(app, client):
    res = client.get("/api/records/export/csv")
    assert res.status_code == 200
    text = res.data.decode("utf-8-sig")
    assert "id," in text
