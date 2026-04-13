from flask import Blueprint

from app.utils.response_helpers import success_response

bp = Blueprint("api_health", __name__)


@bp.route("/health", methods=["GET"])
def health():
    return success_response({"status": "ok", "service": "weather-backend-app"})
