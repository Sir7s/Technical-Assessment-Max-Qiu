from datetime import datetime

from app.models.weather_record import WeatherRecord


def apply_weather_to_record(
    record: WeatherRecord,
    *,
    normalized_location: dict,
    original_input: str,
    query_type: str,
    start_date,
    end_date,
    weather: dict,
    raw_weather_json: str,
    raw_location_json: str,
) -> None:
    record.original_location_input = original_input
    record.resolved_location_name = normalized_location["name"]
    record.latitude = normalized_location["latitude"]
    record.longitude = normalized_location["longitude"]
    record.country = normalized_location.get("country")
    record.region = normalized_location.get("region")
    record.query_type = query_type
    record.start_date = start_date
    record.end_date = end_date
    record.weather_summary = weather.get("weather_summary")
    record.temperature_c = weather.get("temperature_c")
    record.apparent_temperature_c = weather.get("apparent_temperature_c")
    record.humidity_percent = weather.get("humidity_percent")
    record.wind_speed_kmh = weather.get("wind_speed_kmh")
    record.precipitation_probability_percent = weather.get(
        "precipitation_probability_percent"
    )
    record.visibility_m = weather.get("visibility_m")
    record.uv_index = weather.get("uv_index")
    record.sunrise = weather.get("sunrise")
    record.sunset = weather.get("sunset")
    record.raw_weather_json = raw_weather_json
    record.raw_location_json = raw_location_json
    record.updated_at = datetime.utcnow()
