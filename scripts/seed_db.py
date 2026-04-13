"""Insert a few sample rows for local demos. Run from project root: python scripts/seed_db.py"""

import os
import sys

ROOT = os.path.abspath(os.path.join(os.path.dirname(__file__), ".."))
if ROOT not in sys.path:
    sys.path.insert(0, ROOT)

from datetime import datetime  # noqa: E402

from app import create_app  # noqa: E402
from app.extensions import db  # noqa: E402
from app.models.weather_record import WeatherRecord  # noqa: E402


def main():
    app = create_app()
    with app.app_context():
        if WeatherRecord.query.count() > 0:
            print("Database already has records; skipping seed.")
            return
        samples = [
            WeatherRecord(
                original_location_input="Demo City",
                resolved_location_name="Demo City, Demo Region",
                latitude=51.5,
                longitude=-0.12,
                country="Demo Land",
                region="Demo Region",
                query_type="current",
                weather_summary="Mainly clear",
                temperature_c=18.5,
                apparent_temperature_c=17.0,
                humidity_percent=62.0,
                wind_speed_kmh=14.0,
                precipitation_probability_percent=10.0,
                visibility_m=10000.0,
                uv_index=4.0,
                sunrise="2026-04-13T06:10",
                sunset="2026-04-13T19:45",
                raw_weather_json="{}",
                raw_location_json="{}",
                created_at=datetime.utcnow(),
                updated_at=datetime.utcnow(),
            ),
        ]
        for row in samples:
            db.session.add(row)
        db.session.commit()
        print(f"Seeded {len(samples)} record(s).")


if __name__ == "__main__":
    main()
