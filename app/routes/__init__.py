def register_blueprints(app):
    from app.routes.api_health import bp as health_bp
    from app.routes.api_location import bp as location_bp
    from app.routes.api_records import bp as records_bp
    from app.routes.api_weather import bp as weather_bp
    from app.routes.web import bp as web_bp

    app.register_blueprint(health_bp, url_prefix="/api")
    app.register_blueprint(weather_bp, url_prefix="/api/weather")
    app.register_blueprint(records_bp, url_prefix="/api/records")
    app.register_blueprint(location_bp, url_prefix="/api/location")
    app.register_blueprint(web_bp)
