# Weather Backend Demo

Backend-first weather demo for a PM Accelerator assessment: **Flask**, **SQLite**, **SQLAlchemy**, **Open-Meteo** (weather + geocoding), plus a **minimal Jinja + vanilla JS** UI.

This is intended for **local demonstration**, not production deployment.

## Features

- Smart location input: city/postal text, `lat, lon`, or browser geolocation
- Current weather and **forecast** queries with a **bounded** date range (aligned with Open-Meteo’s forecast horizon)
- Successful queries are **auto-saved** as rows in SQLite
- **CRUD** APIs for saved records (updates re-resolve location and **refresh** weather)
- **CSV export** of flattened fields
- OpenStreetMap link for location context

## Stack

- Python 3.11+ recommended
- Flask, Flask-SQLAlchemy, requests
- pytest for automated tests

## Setup

```bash
python -m venv .venv
.venv\Scripts\activate
pip install -r requirements.txt
```

The SQLite file is created at `instance/app.db` on first run.

## Run locally

```bash
python run.py
```

Open `http://127.0.0.1:5000/` for the demo page. Health check: `GET http://127.0.0.1:5000/api/health`.

## Optional seed data

```bash
python scripts/seed_db.py
```

## Tests

```bash
pytest
```

External HTTP is **mocked** in tests so they do not require network access.

## API overview

| Method | Path | Description |
|--------|------|-------------|
| GET | `/api/health` | Service status |
| POST | `/api/weather/query` | Resolve location, fetch weather, **save** record |
| GET | `/api/records` | List saved records (newest first) |
| GET | `/api/records/<id>` | Single record (+ map link) |
| PUT | `/api/records/<id>` | Change query inputs, re-fetch weather |
| DELETE | `/api/records/<id>` | Delete record |
| GET | `/api/records/export/csv` | Download CSV (headers only if empty) |
| GET | `/api/location/resolve?query=...` | Debug geocoding / coordinate parsing |

### `POST /api/weather/query` body (JSON)

- `location_input` (string): city, postal-style text, or coordinates — required unless using current location
- `use_current_location` (bool): when true, send `latitude` and `longitude` from the browser
- `start_date`, `end_date` (optional `YYYY-MM-DD`): omit both for **current** weather; provide **both** for **forecast** range

### Forecast semantics

- Forecast rows store **representative** metrics from the **start date** of the requested range (full series remains in `raw_weather_json`).
- Supported window is limited (default **16 days** ahead, configurable via `Config.MAX_FORECAST_DAYS`).

## Demo flow

1. Search a city or coordinates on `/`.
2. Use **Use my current location** (browser permission required).
3. Optionally set **start** and **end** for a forecast slice.
4. Inspect **Saved history**; use **Update / delete** with a record id for API-style CRUD.
5. **Download CSV** for export.

## Assumptions and limitations

- No authentication; do not expose this on the public internet without hardening.
- Free APIs may omit or vary some fields (e.g. visibility) depending on availability.
- Ambiguous place names may return an error asking for a more specific query.
- Environment variables: optional `DATABASE_URL` and `SECRET_KEY` for non-default local setups.

## Author

Max Qiu — PM Accelerator technical assessment submission.
