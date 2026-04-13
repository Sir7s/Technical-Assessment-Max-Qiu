from datetime import date, datetime

from app.extensions import db


class WeatherRecord(db.Model):
    __tablename__ = "weather_records"

    id = db.Column(db.Integer, primary_key=True)
    created_at = db.Column(db.DateTime, default=datetime.utcnow, nullable=False)
    updated_at = db.Column(
        db.DateTime, default=datetime.utcnow, onupdate=datetime.utcnow, nullable=False
    )

    original_location_input = db.Column(db.String(512), nullable=False)
    resolved_location_name = db.Column(db.String(512), nullable=False)
    latitude = db.Column(db.Float, nullable=False)
    longitude = db.Column(db.Float, nullable=False)
    country = db.Column(db.String(128), nullable=True)
    region = db.Column(db.String(128), nullable=True)

    query_type = db.Column(db.String(32), nullable=False)  # current | forecast
    start_date = db.Column(db.Date, nullable=True)
    end_date = db.Column(db.Date, nullable=True)

    weather_summary = db.Column(db.String(512), nullable=True)
    temperature_c = db.Column(db.Float, nullable=True)
    apparent_temperature_c = db.Column(db.Float, nullable=True)
    humidity_percent = db.Column(db.Float, nullable=True)
    wind_speed_kmh = db.Column(db.Float, nullable=True)
    precipitation_probability_percent = db.Column(db.Float, nullable=True)
    visibility_m = db.Column(db.Float, nullable=True)
    uv_index = db.Column(db.Float, nullable=True)
    sunrise = db.Column(db.String(64), nullable=True)
    sunset = db.Column(db.String(64), nullable=True)

    raw_weather_json = db.Column(db.Text, nullable=True)
    raw_location_json = db.Column(db.Text, nullable=True)

    def to_dict(self):
        return {
            "id": self.id,
            "created_at": self.created_at.isoformat() + "Z" if self.created_at else None,
            "updated_at": self.updated_at.isoformat() + "Z" if self.updated_at else None,
            "original_location_input": self.original_location_input,
            "resolved_location_name": self.resolved_location_name,
            "latitude": self.latitude,
            "longitude": self.longitude,
            "country": self.country,
            "region": self.region,
            "query_type": self.query_type,
            "start_date": self.start_date.isoformat() if self.start_date else None,
            "end_date": self.end_date.isoformat() if self.end_date else None,
            "weather_summary": self.weather_summary,
            "temperature_c": self.temperature_c,
            "apparent_temperature_c": self.apparent_temperature_c,
            "humidity_percent": self.humidity_percent,
            "wind_speed_kmh": self.wind_speed_kmh,
            "precipitation_probability_percent": self.precipitation_probability_percent,
            "visibility_m": self.visibility_m,
            "uv_index": self.uv_index,
            "sunrise": self.sunrise,
            "sunset": self.sunset,
        }
