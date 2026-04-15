# PM Accelerator Tech Assessment #2 — Weather Backend Demo

## Project summary

This repository is a **submission for PM Accelerator Tech Assessment #2 (Backend Engineer)**. It implements a **backend-first** weather application: the primary surface area is **JSON APIs** backed by **real HTTP calls** to Open-Meteo; a **minimal** demo UI (**Jinja2** templates plus **vanilla JavaScript**) is included so reviewers can exercise the system quickly in a browser.

**Stack:** Flask · SQLite · SQLAlchemy · Open-Meteo (geocoding + forecast API) · Jinja + vanilla JS (local demo only).

---

## How this satisfies Tech Assessment #2

| Requirement | How it is addressed in this project |
|-------------|-------------------------------------|
| **Real weather retrieval** | Current and forecast data are fetched from **Open-Meteo** using resolved coordinates (`app/services/weather_service.py`). |
| **CRUD** | **Create** via `POST /api/weather/query` (auto-save on success); **Read** via list and detail routes; **Update** via `PUT /api/records/<id>` (re-runs the same query pipeline); **Delete** via `DELETE /api/records/<id>`. |
| **Persistence** | Rows are stored in **SQLite** via SQLAlchemy model `WeatherRecord` (`instance/app.db`). |
| **Validation** | Location, coordinate, and date-range rules are enforced before external calls (`app/utils/`, `app/services/query_orchestration.py`). |
| **CSV export** | `GET /api/records/export/csv` returns flattened columns (`app/services/export_service.py`). |
| **Extra integration** | Each weather response includes an **OpenStreetMap** link derived from lat/lon (`app/utils/map_helpers.py`); detail responses add `map_link` where applicable. |

---

## Features

- Single **smart location** input: free text (city / postal-style text), parsed **coordinates**, or **browser geolocation** (`use_current_location` + lat/lon).
- **Current** weather when **no** date range is supplied; **forecast** mode when **both** `start_date` and `end_date` are supplied (within a bounded forward window).
- **Automatic persistence** of every successful query as a `WeatherRecord`.
- **Saved history** (newest first), **update** and **delete** by id, **CSV download** of all records.
- **Optional** `GET /api/location/resolve` for debugging geocoding and coordinate parsing without fetching weather.
- **pytest** suite with outbound HTTP **mocked** (no live network required for tests).

---

## Tech stack

| Layer | Technology |
|-------|------------|
| Web framework | Flask 3.x |
| Persistence | SQLite + Flask-SQLAlchemy + SQLAlchemy 2.x |
| External APIs | Open-Meteo (geocoding + forecast) via `requests` |
| Frontend demo | Jinja2 templates, static CSS/JS |
| Testing | pytest |

---

## Architecture (by directory)

| Path | Role |
|------|------|
| `app/routes/` | HTTP layer: JSON blueprints (`api_*`), web route for `/`, thin handlers that delegate to services. |
| `app/services/` | **Geocoding** and **weather** clients, **query orchestration** (`run_weather_query` shared by create and update), **record mapping**, **CSV** serialization. |
| `app/models/` | SQLAlchemy models (`WeatherRecord`). |
| `app/utils/` | Parsers (coordinates, dates), validators (date range, coordinates), JSON **success/error** helpers, OpenStreetMap URL helper. |
| `app/templates/` & `app/static/` | Demo dashboard markup, styles, and client-side `fetch` calls to the JSON API. |

Orchestration is centralized so **routes do not duplicate** resolution or weather-fetch logic: both **`POST /api/weather/query`** and **`PUT /api/records/<id>`** call `run_weather_query`.

---

## Project structure

```text
Technical-Assessment-Max-Qiu/
├── app/
│   ├── __init__.py
│   ├── config.py
│   ├── extensions.py
│   ├── models/
│   │   ├── __init__.py
│   │   └── weather_record.py
│   ├── routes/
│   │   ├── __init__.py
│   │   ├── api_health.py
│   │   ├── api_location.py
│   │   ├── api_records.py
│   │   ├── api_weather.py
│   │   └── web.py
│   ├── services/
│   │   ├── export_service.py
│   │   ├── geocoding_service.py
│   │   ├── query_orchestration.py
│   │   ├── record_service.py
│   │   └── weather_service.py
│   ├── utils/
│   │   ├── map_helpers.py
│   │   ├── parsers.py
│   │   ├── response_helpers.py
│   │   └── validators.py
│   ├── templates/
│   │   ├── base.html
│   │   └── index.html
│   └── static/
│       ├── app.js
│       └── styles.css
├── instance/
│   └── .gitkeep
├── scripts/
│   └── seed_db.py
├── tests/
│   ├── conftest.py
│   ├── test_export_csv.py
│   ├── test_health.py
│   ├── test_records_crud.py
│   └── test_weather_query.py
├── run.py
├── requirements.txt
├── .gitignore
└── README.md
```

---

## Data model: `WeatherRecord`

Each successful weather query produces one row. Stored fields include:

- **Identity / timestamps:** `id`, `created_at`, `updated_at`
- **Inputs / resolution:** `original_location_input`, `resolved_location_name`, `latitude`, `longitude`, optional `country`, `region`
- **Query classification:** `query_type` (`current` or `forecast`), optional `start_date`, `end_date`
- **Denormalized weather snapshot:** `weather_summary`, `temperature_c`, `apparent_temperature_c`, `humidity_percent`, `wind_speed_kmh`, `precipitation_probability_percent`, `visibility_m`, `uv_index`, `sunrise`, `sunset` (availability varies by query mode and API response)
- **Raw payloads (JSON strings):** `raw_weather_json`, `raw_location_json`

For **forecast** queries, flattened metrics represent a **representative snapshot aligned to the start of the requested date range**; the full API payload remains in `raw_weather_json`.

---

## Setup

### Windows (PowerShell)

```powershell
python -m venv .venv
.\.venv\Scripts\Activate.ps1
pip install -r requirements.txt
```

### macOS / Linux

```bash
python3 -m venv .venv
source .venv/bin/activate
pip install -r requirements.txt
```

Optional: set `DATABASE_URL` (override SQLite path) or `SECRET_KEY` (Flask) for non-default local setups.

---

## Run

```bash
python run.py
```

On Linux, use `python3` if `python` is not available.

- **Demo UI:** `http://127.0.0.1:5000/`
- The SQLite database file is created at **`instance/app.db`** on first run (the `instance/` directory is tracked; the `.db` file is gitignored).

### Optional seed data

```bash
python scripts/seed_db.py
```

Skips seeding if records already exist.

---

## Demo flow (for reviewers)

1. Start the app with `python run.py`.
2. Open `http://127.0.0.1:5000/`.
3. Enter a city or coordinates and submit — confirm **current** weather and **saved history** updates.
4. Optionally set **Start** and **End** dates (both required for forecast) and submit.
5. Use **Use my current location** if browser permissions allow.
6. Click **Download CSV** or open `GET /api/records/export/csv` in the browser.
7. Use the **Record ID** section to **update** or **delete** a row, or exercise the same operations via `curl` or an HTTP client.

---

## API overview

| Method | Path | Description |
|--------|------|-------------|
| `GET` | `/api/health` | Liveness / basic service info |
| `GET` | `/api/location/resolve?query=...` | Resolve text or coordinates without calling the weather API |
| `POST` | `/api/weather/query` | Validate input, resolve location, fetch weather, **create** `WeatherRecord` on success (`201`) |
| `GET` | `/api/records` | List all records, newest first |
| `GET` | `/api/records/<id>` | Single record; includes `map_link` |
| `PUT` | `/api/records/<id>` | Same JSON body as query; re-resolve and **replace** stored snapshot |
| `DELETE` | `/api/records/<id>` | Permanently delete record (`404` if missing) |
| `GET` | `/api/records/export/csv` | CSV download; header row always present |

**Success envelope:** `{ "success": true, "data": { ... } }`  
**Error envelope:** `{ "success": false, "error": { "message": "...", "code": "...", "fields": { } } }` (optional `code` / `fields`)

---

## Example JSON request bodies (`POST /api/weather/query` and `PUT /api/records/<id>`)

### Current weather (text location)

```json
{
  "location_input": "London, UK",
  "use_current_location": false,
  "latitude": null,
  "longitude": null,
  "start_date": null,
  "end_date": null
}
```

### Forecast (both dates required; `YYYY-MM-DD`)

```json
{
  "location_input": "Berlin",
  "use_current_location": false,
  "latitude": null,
  "longitude": null,
  "start_date": "2026-04-14",
  "end_date": "2026-04-16"
}
```

### Current weather (browser location)

```json
{
  "location_input": "40.7128, -74.0060",
  "use_current_location": true,
  "latitude": 40.7128,
  "longitude": -74.006
}
```

`use_current_location: true` requires valid `latitude` and `longitude`; `location_input` may be empty and will default to a coordinate label in storage.

---

## Design decisions

- **Flask:** Fits a compact assessment scope: clear routing, JSON responses, and Jinja for a lightweight demo without a separate frontend build pipeline.
- **SQLite:** Zero external database process; single file under `instance/`, easy for reviewers to run locally and reset.
- **Open-Meteo:** No API key for basic usage, suitable for a local demo; provides geocoding and forecast endpoints sufficient for current + bounded future ranges.
- **Successful queries auto-save:** Demonstrates default **create-on-success** persistence and keeps the “happy path” one step for users of the demo UI.
- **Updates re-fetch weather:** `PUT` reuses `run_weather_query` so stored data stays **consistent** with validation and external APIs; manual edits to cached numbers would bypass those rules.
- **Minimal frontend:** The assessment targets **backend** clarity; the UI exists to **trigger** and **visualize** API behavior, not to duplicate business logic.

---

## Validation and error handling

- **Location:** Non-empty text unless `use_current_location` supplies valid coordinates; coordinate strings must parse and fall within valid lat/lon ranges; geocoding must return a result; ambiguous top matches may return `AMBIGUOUS_LOCATION`.
- **Dates:** If either `start_date` or `end_date` is supplied, both must be valid ISO dates; for forecast, `end_date >= start_date`, range must lie within the configured forward horizon (`MAX_FORECAST_DAYS`, default 16); supplying only one date is rejected.
- **HTTP / upstream failures:** Handled with appropriate status codes (e.g. `502` when external requests fail during query).
- **Records:** Missing id returns `404` with `RECORD_NOT_FOUND`.

---

## Testing

```bash
pytest
```

Tests mock outbound HTTP to Open-Meteo so they do not require network access. The test harness disposes the SQLAlchemy engine before removing temporary SQLite files on Windows.

---

## Limitations and tradeoffs

- **Local demo only:** No authentication, no production deployment configuration, no rate limiting.
- **Field availability:** Some metrics (e.g. visibility) may be absent depending on query mode or API payload.
- **Forecast semantics:** Flattened columns summarize a **representative** slice; full series data is retained in `raw_weather_json`.
- **Ambiguity:** Geocoding ambiguity is handled with a conservative heuristic; highly ambiguous names may require a more specific query.

---

## PM Accelerator note

This submission is intended to demonstrate **API integration**, **data modeling**, **validation**, **persistence**, **CRUD**, **export**, and **clear structure** suitable for review within a short time window.

---

## Author

**Max Qiu**  
PM Accelerator Technical Assessment Submission
