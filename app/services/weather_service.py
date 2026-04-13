import json
from datetime import date, datetime, timezone
from typing import Any

import requests

from app.config import Config

FORECAST_URL = "https://api.open-meteo.com/v1/forecast"

# WMO weather interpretation codes (subset labels)
_WMO_LABELS = {
    0: "Clear sky",
    1: "Mainly clear",
    2: "Partly cloudy",
    3: "Overcast",
    45: "Fog",
    48: "Depositing rime fog",
    51: "Light drizzle",
    53: "Moderate drizzle",
    55: "Dense drizzle",
    56: "Light freezing drizzle",
    57: "Dense freezing drizzle",
    61: "Slight rain",
    63: "Moderate rain",
    65: "Heavy rain",
    66: "Light freezing rain",
    67: "Heavy freezing rain",
    71: "Slight snow",
    73: "Moderate snow",
    75: "Heavy snow",
    77: "Snow grains",
    80: "Slight rain showers",
    81: "Moderate rain showers",
    82: "Violent rain showers",
    85: "Slight snow showers",
    86: "Heavy snow showers",
    95: "Thunderstorm",
    96: "Thunderstorm with slight hail",
    99: "Thunderstorm with heavy hail",
}


def _label_for_code(code: int | None) -> str | None:
    if code is None:
        return None
    return _WMO_LABELS.get(int(code), f"Weather code {code}")


def fetch_current_weather(lat: float, lon: float) -> tuple[dict[str, Any], str]:
    params = {
        "latitude": lat,
        "longitude": lon,
        "timezone": "auto",
        "forecast_days": 2,
        "current": ",".join(
            [
                "temperature_2m",
                "relative_humidity_2m",
                "apparent_temperature",
                "weather_code",
                "wind_speed_10m",
                "precipitation_probability",
                "uv_index",
            ]
        ),
        "hourly": "visibility",
        "daily": ",".join(
            [
                "sunrise",
                "sunset",
                "weather_code",
                "uv_index_max",
                "precipitation_probability_max",
            ]
        ),
    }
    r = requests.get(FORECAST_URL, params=params, timeout=25)
    r.raise_for_status()
    data = r.json()
    raw_text = json.dumps(data)
    normalized = _normalize_open_meteo_payload(data, mode="current")
    return normalized, raw_text


def fetch_forecast_range(
    lat: float, lon: float, start: date, end: date
) -> tuple[dict[str, Any], str]:
    """Forecast summary uses the start_date slice as representative scalars."""
    today = date.today()
    days_to_end = (end - today).days + 1
    forecast_days = max(1, min(Config.MAX_FORECAST_DAYS, days_to_end))
    params = {
        "latitude": lat,
        "longitude": lon,
        "timezone": "auto",
        "forecast_days": forecast_days,
        "daily": ",".join(
            [
                "weather_code",
                "temperature_2m_max",
                "temperature_2m_min",
                "apparent_temperature_max",
                "apparent_temperature_min",
                "precipitation_probability_max",
                "uv_index_max",
                "sunrise",
                "sunset",
                "wind_speed_10m_max",
            ]
        ),
    }
    r = requests.get(FORECAST_URL, params=params, timeout=25)
    r.raise_for_status()
    data = r.json()
    raw_text = json.dumps(data)
    normalized = _normalize_open_meteo_payload(
        data,
        mode="forecast",
        range_start=start,
        range_end=end,
        today=today,
    )
    return normalized, raw_text


def _normalize_open_meteo_payload(
    data: dict,
    mode: str,
    range_start: date | None = None,
    range_end: date | None = None,
    today: date | None = None,
) -> dict[str, Any]:
    daily = data.get("daily") or {}
    times = daily.get("time") or []

    if mode == "current":
        cur = data.get("current") or {}
        hourly = data.get("hourly") or {}
        vis_m = _pick_hourly_visibility(hourly, data.get("utc_offset_seconds"))
        daily_wcode = (daily.get("weather_code") or [None])[0]
        sunrise = _fmt_time((daily.get("sunrise") or [None])[0])
        sunset = _fmt_time((daily.get("sunset") or [None])[0])
        wcode = cur.get("weather_code")
        if wcode is None:
            wcode = daily_wcode
        summary = _label_for_code(int(wcode)) if wcode is not None else None
        precip = cur.get("precipitation_probability")
        if precip is None:
            precip = (daily.get("precipitation_probability_max") or [None])[0]
        uv = cur.get("uv_index")
        if uv is None:
            uv = (daily.get("uv_index_max") or [None])[0]

        return {
            "mode": "current",
            "weather_summary": summary,
            "temperature_c": cur.get("temperature_2m"),
            "apparent_temperature_c": cur.get("apparent_temperature"),
            "humidity_percent": cur.get("relative_humidity_2m"),
            "wind_speed_kmh": cur.get("wind_speed_10m"),
            "precipitation_probability_percent": precip,
            "visibility_m": vis_m,
            "uv_index": uv,
            "sunrise": sunrise,
            "sunset": sunset,
            "weather_code": wcode,
        }

    # forecast mode: representative day = start of requested range
    idx = 0
    if range_start and times:
        rs = range_start.isoformat()
        try:
            idx = times.index(rs)
        except ValueError:
            idx = _nearest_daily_index(times, range_start, today)

    wcode = (daily.get("weather_code") or [None])[idx]
    tmax = (daily.get("temperature_2m_max") or [None])[idx]
    tmin = (daily.get("temperature_2m_min") or [None])[idx]
    amax = (daily.get("apparent_temperature_max") or [None])[idx]
    amin = (daily.get("apparent_temperature_min") or [None])[idx]
    t_rep = tmax if tmax is not None else tmin
    at_rep = amax if amax is not None else amin
    precip = (daily.get("precipitation_probability_max") or [None])[idx]
    uv = (daily.get("uv_index_max") or [None])[idx]
    wind = (daily.get("wind_speed_10m_max") or [None])[idx]
    sunrise = _fmt_time((daily.get("sunrise") or [None])[idx])
    sunset = _fmt_time((daily.get("sunset") or [None])[idx])

    summary = _label_for_code(int(wcode)) if wcode is not None else None
    if range_start and range_end and range_start != range_end:
        summary = (
            f"{summary or 'Forecast'} "
            f"({range_start.isoformat()} to {range_end.isoformat()}; "
            f"representative: {range_start.isoformat()})"
        )
    elif summary and range_start:
        summary = f"{summary} ({range_start.isoformat()})"

    return {
        "mode": "forecast",
        "weather_summary": summary,
        "temperature_c": t_rep,
        "apparent_temperature_c": at_rep,
        "humidity_percent": None,
        "wind_speed_kmh": wind,
        "precipitation_probability_percent": precip,
        "visibility_m": None,
        "uv_index": uv,
        "sunrise": sunrise,
        "sunset": sunset,
        "weather_code": wcode,
    }


def _fmt_time(val) -> str | None:
    if val is None:
        return None
    if isinstance(val, str):
        return val
    return str(val)


def _pick_hourly_visibility(hourly: dict, utc_offset_seconds: int | None) -> float | None:
    times = hourly.get("time") or []
    vis = hourly.get("visibility") or []
    if not times or not vis:
        return None
    now = datetime.now(timezone.utc)
    best_i = 0
    best_diff = None
    for i, t in enumerate(times):
        try:
            # hourly times are ISO without Z sometimes
            ts = t.replace("Z", "+00:00") if "Z" in t else t
            dt = datetime.fromisoformat(ts)
            if dt.tzinfo is None:
                dt = dt.replace(tzinfo=timezone.utc)
            diff = abs((dt - now).total_seconds())
        except (ValueError, TypeError):
            continue
        if best_diff is None or diff < best_diff:
            best_diff = diff
            best_i = i
    try:
        return float(vis[best_i])
    except (IndexError, TypeError, ValueError):
        return None


def _nearest_daily_index(
    time_strings: list, target: date, today: date | None
) -> int:
    """Pick closest daily index to target when exact match is missing."""
    if not time_strings:
        return 0
    best = 0
    best_delta = None
    for i, t in enumerate(time_strings):
        try:
            d = date.fromisoformat(str(t)[:10])
        except ValueError:
            continue
        delta = abs((d - target).days)
        if best_delta is None or delta < best_delta:
            best_delta = delta
            best = i
    return best
