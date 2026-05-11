import sys
import os
import logging

from flask import Flask

# Add paths for shared library
sys.path.insert(0, os.path.join(os.path.dirname(__file__), ".."))
sys.path.insert(0, os.path.join(os.path.dirname(__file__), "..", ".."))

from app.config import Config
from app.extensions import db
from app.routes import inventory_bp
from app.events import start_consumer
from shared.health import create_health_blueprint
from shared.logging_config import correlation_id_middleware, setup_logging
from shared.messaging import RabbitMQConnection

logger = logging.getLogger(__name__)


def create_app(config_class=Config) -> Flask:
    app = Flask(__name__)
    app.config.from_object(config_class)

    # Initialize structured logging
    setup_logging(
        service_name=app.config.get("SERVICE_NAME", "inventory-service"),
        level=app.config.get("LOG_LEVEL", "INFO"),
    )

    # Initialize extensions
    db.init_app(app)

    # Register middleware
    correlation_id_middleware(app)

    # Register blueprints
    app.register_blueprint(inventory_bp)

    def check_db():
        try:
            db.session.execute(db.text("SELECT 1"))
            return True
        except Exception:
            return False

    health_bp = create_health_blueprint(
        service_name=app.config.get("SERVICE_NAME", "inventory-service"),
        check_db=check_db,
    )
    app.register_blueprint(health_bp)

    # Create tables
    with app.app_context():
        db.create_all()

    # Start RabbitMQ consumer
    if not app.config.get("TESTING"):
        try:
            rmq = RabbitMQConnection(
                url=app.config["RABBITMQ_URL"],
                service_name=app.config.get("SERVICE_NAME", "inventory-service"),
            )
            start_consumer(app, rmq)
        except Exception:
            logger.warning("Could not start RabbitMQ consumer (will retry on restart)")

    logger.info("Inventory service initialized")
    return app


if __name__ == "__main__":
    app = create_app()
    app.run(host="0.0.0.0", port=8000, debug=False)
