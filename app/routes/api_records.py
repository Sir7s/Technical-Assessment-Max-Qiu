import requests
from flask import Blueprint, make_response, request

from app.extensions import db
from app.models.weather_record import WeatherRecord
from app.services.export_service import records_to_csv_bytes
from app.services.query_orchestration import (
    error_message_for_code,
    run_weather_query,
)
from app.services.record_service import apply_weather_to_record
from app.utils.map_helpers import openstreetmap_link
from app.utils.response_helpers import error_response, success_response
from app.utils.validators import date_range_error_detail

bp = Blueprint("api_records", __name__)


def _detail(record: WeatherRecord) -> dict:
    data = record.to_dict()
    data["map_link"] = openstreetmap_link(record.latitude, record.longitude)
    return data


@bp.route("/export/csv", methods=["GET"])
def export_csv():
    rows = WeatherRecord.query.order_by(WeatherRecord.created_at.desc()).all()
    data = records_to_csv_bytes(rows)
    resp = make_response(data)
    resp.headers["Content-Type"] = "text/csv; charset=utf-8"
    resp.headers["Content-Disposition"] = 'attachment; filename="weather_records.csv"'
    return resp


@bp.route("", methods=["GET"])
def list_records():
    rows = (
        WeatherRecord.query.order_by(WeatherRecord.created_at.desc()).all()
    )
    return success_response({"records": [r.to_dict() for r in rows]})


@bp.route("/<int:record_id>", methods=["GET"])
def get_record(record_id: int):
    record = db.session.get(WeatherRecord, record_id)
    if not record:
        return error_response("Record not found.", code="RECORD_NOT_FOUND", status=404)
    return success_response({"record": _detail(record)})


@bp.route("/<int:record_id>", methods=["PUT"])
def update_record(record_id: int):
    record = db.session.get(WeatherRecord, record_id)
    if not record:
        return error_response("Record not found.", code="RECORD_NOT_FOUND", status=404)

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
    try:
        db.session.commit()
    except Exception:
        db.session.rollback()
        return error_response(
            "Could not update the weather record.",
            code="EXTERNAL_API_ERROR",
            status=500,
        )

    return success_response(
        {
            "record": _detail(record),
            "weather": {
                **result.weather,
                "map_link": openstreetmap_link(
                    result.normalized_location["latitude"],
                    result.normalized_location["longitude"],
                ),
            },
        }
    )


@bp.route("/<int:record_id>", methods=["DELETE"])
def delete_record(record_id: int):
    record = db.session.get(WeatherRecord, record_id)
    if not record:
        return error_response("Record not found.", code="RECORD_NOT_FOUND", status=404)
    db.session.delete(record)
    db.session.commit()
    return success_response({"deleted_id": record_id})
