import sys
import os
import logging

from flask import Flask

# Add parent of 'app' to path so 'shared' package is importable
# Works both locally (project root) and in Docker (/app)
sys.path.insert(0, os.path.join(os.path.dirname(__file__), ".."))
sys.path.insert(0, os.path.join(os.path.dirname(__file__), "..", ".."))

from app.config import Config
from app.extensions import db
from app.routes import products_bp
from shared.health import create_health_blueprint
from shared.logging_config import correlation_id_middleware, setup_logging
from shared.metrics_flask import setup_flask_metrics
from shared.tracing_flask import setup_flask_tracing

logger = logging.getLogger(__name__)


def create_app(config_class=Config) -> Flask:
    app = Flask(__name__)
    app.config.from_object(config_class)

    # Initialize structured logging
    setup_logging(
        service_name=app.config.get("SERVICE_NAME", "product-service"),
        level=app.config.get("LOG_LEVEL", "INFO"),
    )

    # Initialize extensions
    db.init_app(app)

    # Register middleware
    correlation_id_middleware(app)
    setup_flask_metrics(app, app.config.get("SERVICE_NAME", "product-service"))
    setup_flask_tracing(app, app.config.get("SERVICE_NAME", "product-service"))

    # Register blueprints
    app.register_blueprint(products_bp)

    def check_db():
        try:
            db.session.execute(db.text("SELECT 1"))
            return True
        except Exception:
            return False

    health_bp = create_health_blueprint(
        service_name=app.config.get("SERVICE_NAME", "product-service"),
        check_db=check_db,
    )
    app.register_blueprint(health_bp)

    # Create tables on first request (migrations preferred for production)
    with app.app_context():
        db.create_all()

    logger.info("Product service initialized")
    return app


def get_app():
    """Lazy app factory for gunicorn / module-level import."""
    return create_app()


# Only create the app when running directly or via gunicorn (not during test import)
app = None


def _get_or_create_app():
    global app
    if app is None:
        app = create_app()
    return app


if __name__ == "__main__":
    app = create_app()
    app.run(host="0.0.0.0", port=8000, debug=False)
