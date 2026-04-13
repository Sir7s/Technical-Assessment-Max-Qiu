def openstreetmap_link(latitude: float, longitude: float, zoom: int = 12) -> str:
    return f"https://www.openstreetmap.org/?mlat={latitude}&mlon={longitude}#map={zoom}/{latitude}/{longitude}"
