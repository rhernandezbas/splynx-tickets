from flask import Flask, request
from app.utils.config import db, migrate, Config

def create_app() -> Flask:
    """Application factory for the app."""
    app = Flask(__name__)

    app.config.from_object(Config)  # Load config from a file
    db.init_app(app)
    migrate.init_app(app, db)

    # Register blueprints
    from app.routes import blueprint as routes_bp
    app.register_blueprint(routes_bp)
    
    # Inicializar scheduler inmediatamente al crear la app
    from app.scheduler import init_scheduler
    init_scheduler(app)

    # Minimal CORS for development
    @app.after_request
    def add_cors_headers(response):
        origin = request.headers.get("Origin") or "*"
        response.headers["Access-Control-Allow-Origin"] = origin
        response.headers["Vary"] = "Origin"
        response.headers["Access-Control-Allow-Credentials"] = "true"
        response.headers["Access-Control-Allow-Headers"] = "Content-Type, Authorization"
        response.headers["Access-Control-Allow-Methods"] = "GET, POST, PUT, DELETE, OPTIONS"
        return response

    @app.before_request
    def handle_options_preflight():
        if request.method == "OPTIONS":
            # Short-circuit CORS preflight
            resp = app.make_default_options_response()
            origin = request.headers.get("Origin") or "*"
            resp.headers["Access-Control-Allow-Origin"] = origin
            resp.headers["Vary"] = "Origin"
            resp.headers["Access-Control-Allow-Credentials"] = "true"
            resp.headers["Access-Control-Allow-Headers"] = "Content-Type, Authorization"
            resp.headers["Access-Control-Allow-Methods"] = "GET, POST, PUT, DELETE, OPTIONS"
            return resp

    return app


# Allow running with: python -m app
if __name__ == "__main__":
    app = create_app()
    app.run(host="0.0.0.0", port=5605, debug=True)