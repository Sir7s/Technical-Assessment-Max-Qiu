import re
from datetime import date


_COORD_PATTERNS = [
    re.compile(
        r"^\s*([+-]?\d+(?:\.\d+)?)\s*[,;]\s*([+-]?\d+(?:\.\d+)?)\s*$"
    ),
    re.compile(
        r"^\s*([+-]?\d+(?:\.\d+)?)\s+([+-]?\d+(?:\.\d+)?)\s*$"
    ),
]


def parse_coordinates(text: str) -> tuple[float, float] | None:
    if not text or not text.strip():
        return None
    s = text.strip()
    for pat in _COORD_PATTERNS:
        m = pat.match(s)
        if not m:
            continue
        lat = float(m.group(1))
        lon = float(m.group(2))
        if -90 <= lat <= 90 and -180 <= lon <= 180:
            return lat, lon
    return None


def parse_iso_date(value) -> date | None:
    if value is None or value == "":
        return None
    if isinstance(value, date):
        return value
    if not isinstance(value, str):
        return None
    s = value.strip()
    if not s:
        return None
    try:
        parts = s.split("T")[0]
        y, m, d = (int(x) for x in parts.split("-")[:3])
        return date(y, m, d)
    except (ValueError, TypeError):
        return None
