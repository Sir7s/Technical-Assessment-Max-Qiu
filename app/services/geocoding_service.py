import json
from typing import Any

import requests

GEOCODE_URL = "https://geocoding-api.open-meteo.com/v1/search"


def search_location(query: str, count: int = 8) -> dict[str, Any]:
    params = {"name": query.strip(), "count": count, "language": "en"}
    r = requests.get(GEOCODE_URL, params=params, timeout=20)
    r.raise_for_status()
    return r.json()


def resolve_from_text(query: str) -> tuple[dict[str, Any], str]:
    """
    Returns (normalized_location_dict, raw_json_string).
    normalized keys: name, latitude, longitude, country, region, raw_result
    Raises ValueError with code LOCATION_NOT_FOUND or AMBIGUOUS_LOCATION
    """
    raw = search_location(query)
    raw_text = json.dumps(raw)
    results = raw.get("results") or []
    if not results:
        raise ValueError("LOCATION_NOT_FOUND")

    top = results[0]
    # If multiple strong matches with very different coordinates, surface ambiguity
    if len(results) >= 2:
        second = results[1]
        if _distinct_places(top, second):
            raise ValueError("AMBIGUOUS_LOCATION")

    name = top.get("name") or query
    admin = top.get("admin1")
    country = top.get("country")
    parts = [p for p in [name, admin, country] if p]
    display = ", ".join(parts) if parts else name

    normalized = {
        "name": display,
        "latitude": float(top["latitude"]),
        "longitude": float(top["longitude"]),
        "country": country,
        "region": admin,
    }
    return normalized, raw_text


def _distinct_places(a: dict, b: dict) -> bool:
    """Heuristic: two different countries or large distance → ambiguous."""
    if a.get("country") and b.get("country") and a.get("country") != b.get("country"):
        return True
    lat_a, lon_a = float(a["latitude"]), float(a["longitude"])
    lat_b, lon_b = float(b["latitude"]), float(b["longitude"])
    # ~50 km threshold (very rough)
    dlat = abs(lat_a - lat_b)
    dlon = abs(lon_a - lon_b)
    return (dlat**2 + dlon**2) ** 0.5 > 0.5
