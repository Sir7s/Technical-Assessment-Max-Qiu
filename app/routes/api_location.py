import json

from flask import Blueprint, request

from app.services import geocoding_service
from app.utils.parsers import parse_coordinates
from app.utils.response_helpers import error_response, success_response

bp = Blueprint("api_location", __name__)


@bp.route("/resolve", methods=["GET"])
def resolve():
    q = (request.args.get("query") or "").strip()
    if not q:
        return error_response(
            "Query parameter `query` is required.",
            code="INVALID_LOCATION_INPUT",
            status=400,
        )
    coord = parse_coordinates(q)
    if coord:
        lat, lon = coord
        return success_response(
            {
                "mode": "coordinates",
                "latitude": lat,
                "longitude": lon,
                "display_name": f"{lat:.4f}, {lon:.4f}",
            }
        )
    try:
        normalized, raw = geocoding_service.resolve_from_text(q)
    except ValueError as exc:
        code = str(exc)
        if code == "LOCATION_NOT_FOUND":
            return error_response(
                "No location matched that search.",
                code="LOCATION_NOT_FOUND",
                status=404,
            )
        if code == "AMBIGUOUS_LOCATION":
            return error_response(
                "Multiple distinct places matched. Refine your search.",
                code="AMBIGUOUS_LOCATION",
                status=409,
            )
        return error_response("Unable to resolve location.", status=400)

    return success_response(
        {
            "mode": "geocoded",
            "display_name": normalized["name"],
            "latitude": normalized["latitude"],
            "longitude": normalized["longitude"],
            "country": normalized.get("country"),
            "region": normalized.get("region"),
            "raw": json.loads(raw),
        }
    )
