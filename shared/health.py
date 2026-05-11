import time
from flask import Blueprint, jsonify


def create_health_blueprint(
    service_name: str,
    check_db: callable = None,
    check_rabbitmq: callable = None,
):
    """Create a health check blueprint for Flask services.

    Args:
        service_name: Name of the service.
        check_db: Optional callable that returns True if DB is healthy.
        check_rabbitmq: Optional callable that returns True if RabbitMQ is healthy.
    """
    health_bp = Blueprint("health", __name__)
    start_time = time.time()

    @health_bp.route("/health")
    def health():
        return jsonify({"status": "ok", "service": service_name}), 200

    @health_bp.route("/ready")
    def ready():
        checks = {}
        all_ok = True

        if check_db:
            try:
                db_ok = check_db()
                checks["database"] = "ok" if db_ok else "error"
                if not db_ok:
                    all_ok = False
            except Exception as e:
                checks["database"] = str(e)
                all_ok = False

        if check_rabbitmq:
            try:
                rmq_ok = check_rabbitmq()
                checks["rabbitmq"] = "ok" if rmq_ok else "error"
                if not rmq_ok:
                    all_ok = False
            except Exception as e:
                checks["rabbitmq"] = str(e)
                all_ok = False

        uptime = time.time() - start_time
        status_code = 200 if all_ok else 503
        return (
            jsonify(
                {
                    "status": "ok" if all_ok else "degraded",
                    "service": service_name,
                    "uptime_seconds": round(uptime, 1),
                    "checks": checks,
                }
            ),
            status_code,
        )

    return health_bp
