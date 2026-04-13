import requests
from flask import Blueprint, request

from app.extensions import db
from app.models.weather_record import WeatherRecord
from app.services.query_orchestration import error_message_for_code, run_weather_query
from app.services.record_service import apply_weather_to_record
from app.utils.map_helpers import openstreetmap_link
from app.utils.response_helpers import error_response, success_response
from app.utils.validators import date_range_error_detail

bp = Blueprint("api_weather", __name__)


def _enrich_weather_payload(weather: dict, lat: float, lon: float) -> dict:
    out = dict(weather)
    out["map_link"] = openstreetmap_link(lat, lon)
    return out


@bp.route("/query", methods=["POST"])
def query():
    body = request.get_json(silent=True)
    if not isinstance(body, dict):
        body = {}
    try:
        result = run_weather_query(body)
    except ValueError as exc:
        key = str(exc)
        if key == "INVALID_DATE_FORMAT":
            msg, err_code = error_message_for_code(key)
            return error_response(msg, code=err_code, status=400)
        if key in (
            "MISSING_DATES",
            "INCOMPLETE_DATE_RANGE",
            "END_BEFORE_START",
            "START_BEFORE_TODAY",
            "RANGE_BEYOND_FORECAST",
        ):
            msg, err_code = date_range_error_detail(key)
            fields = None
            if key == "END_BEFORE_START":
                fields = {"end_date": "Must be on or after start_date."}
            return error_response(msg, code=err_code, fields=fields, status=400)
        msg, err_code = error_message_for_code(key)
        return error_response(msg, code=err_code, status=400)
    except requests.RequestException:
        return error_response(
            "The weather service did not respond. Try again shortly.",
            code="EXTERNAL_API_ERROR",
            status=502,
        )

    record = WeatherRecord()
    apply_weather_to_record(
        record,
        normalized_location=result.normalized_location,
        original_input=result.original_location_input,
        query_type=result.query_type,
        start_date=result.start_date,
        end_date=result.end_date,
        weather=result.weather,
        raw_weather_json=result.raw_weather_json,
        raw_location_json=result.raw_location_json,
    )
    db.session.add(record)
    try:
        db.session.commit()
    except Exception:
        db.session.rollback()
        return error_response(
            "Could not save the weather record.",
            code="EXTERNAL_API_ERROR",
            status=500,
        )

    payload = {
        "record": record.to_dict(),
        "weather": _enrich_weather_payload(
            result.weather,
            result.normalized_location["latitude"],
            result.normalized_location["longitude"],
        ),
    }
    return success_response(payload, status=201)
