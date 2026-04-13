from flask import Blueprint, render_template

from app.config import Config

bp = Blueprint("web", __name__)


@bp.route("/")
def index():
    return render_template("index.html", max_forecast_days=Config.MAX_FORECAST_DAYS)
