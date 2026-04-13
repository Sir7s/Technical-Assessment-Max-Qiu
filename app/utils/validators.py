from datetime import date, timedelta

from app.config import Config


def validate_coordinate_pair(lat, lon) -> tuple[float, float] | None:
    if lat is None or lon is None:
        return None
    try:
        lat_f = float(lat)
        lon_f = float(lon)
    except (TypeError, ValueError):
        return None
    if not (-90 <= lat_f <= 90 and -180 <= lon_f <= 180):
        return None
    return lat_f, lon_f


def validate_date_range_for_forecast(
    start: date | None,
    end: date | None,
    today: date,
    max_days: int | None = None,
):
    """
    Returns (start_date, end_date) or raises ValueError with message + code.
    """
    max_days = max_days or Config.MAX_FORECAST_DAYS
    if start is None and end is None:
        raise ValueError("MISSING_DATES")
    if start is None or end is None:
        raise ValueError("INCOMPLETE_DATE_RANGE")
    if end < start:
        raise ValueError("END_BEFORE_START")
    last_allowed = today + timedelta(days=max_days - 1)
    if start < today:
        raise ValueError("START_BEFORE_TODAY")
    if end > last_allowed:
        raise ValueError("RANGE_BEYOND_FORECAST")
    return start, end


def date_range_error_detail(exc_code: str) -> tuple[str, str]:
    messages = {
        "MISSING_DATES": (
            "Both start_date and end_date are required for a forecast query.",
            "INVALID_DATE_RANGE",
        ),
        "INCOMPLETE_DATE_RANGE": (
            "Provide both start_date and end_date, or omit both for current weather.",
            "INVALID_DATE_RANGE",
        ),
        "END_BEFORE_START": (
            "end_date must be on or after start_date.",
            "INVALID_DATE_RANGE",
        ),
        "START_BEFORE_TODAY": (
            "Forecast dates must be today or later.",
            "INVALID_DATE_RANGE",
        ),
        "RANGE_BEYOND_FORECAST": (
            f"Forecast range must fall within the next {Config.MAX_FORECAST_DAYS} days.",
            "FORECAST_RANGE_UNSUPPORTED",
        ),
    }
    return messages.get(exc_code, ("Invalid date range.", "INVALID_DATE_RANGE"))
