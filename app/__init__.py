import os

from flask import Flask

from app.config import Config
from app.extensions import db


def create_app(config_class=Config):
    app = Flask(
        __name__,
        template_folder="templates",
        static_folder="static",
        instance_relative_config=True,
    )
    app.config.from_object(config_class)

    instance_path = os.path.join(os.path.dirname(app.root_path), "instance")
    os.makedirs(instance_path, exist_ok=True)

    db.init_app(app)

    from app.routes import register_blueprints

    register_blueprints(app)

    with app.app_context():
        db.create_all()

    return app
