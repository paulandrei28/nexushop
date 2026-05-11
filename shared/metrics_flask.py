"""Flask middleware for Prometheus request metrics."""

import time
from shared.metrics import (
    REQUEST_COUNT,
    REQUEST_LATENCY,
    REQUESTS_IN_PROGRESS,
    SERVICE_INFO,
    get_metrics,
    get_metrics_content_type,
)


def setup_flask_metrics(app, service_name):
    """Add Prometheus metrics collection to a Flask app."""
    SERVICE_INFO.info({"name": service_name, "framework": "flask"})

    @app.before_request
    def _before():
        from flask import request, g

        g.start_time = time.time()
        REQUESTS_IN_PROGRESS.labels(service=service_name).inc()

    @app.after_request
    def _after(response):
        from flask import request, g

        REQUESTS_IN_PROGRESS.labels(service=service_name).dec()
        endpoint = request.path
        # Normalize IDs in paths to keep cardinality low
        parts = endpoint.split("/")
        normalized = "/".join("{id}" if _looks_like_id(p) else p for p in parts)
        latency = time.time() - getattr(g, "start_time", time.time())
        REQUEST_COUNT.labels(
            service=service_name,
            method=request.method,
            endpoint=normalized,
            status_code=response.status_code,
        ).inc()
        REQUEST_LATENCY.labels(
            service=service_name,
            method=request.method,
            endpoint=normalized,
        ).observe(latency)
        return response

    @app.route("/metrics")
    def metrics_endpoint():
        from flask import Response

        return Response(
            get_metrics(),
            content_type=get_metrics_content_type(),
        )


def _looks_like_id(segment):
    """Check if a URL segment looks like a UUID or numeric ID."""
    if not segment:
        return False
    if len(segment) >= 20:
        return True
    if segment.isdigit():
        return True
    # UUID pattern
    if len(segment) == 36 and segment.count("-") == 4:
        return True
    return False
