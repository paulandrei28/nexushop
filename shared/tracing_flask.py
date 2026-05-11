"""Flask middleware for OpenTelemetry tracing."""

import logging

logger = logging.getLogger(__name__)


def setup_flask_tracing(app, service_name: str):
    """Add OpenTelemetry tracing to a Flask app."""
    from shared.tracing import setup_tracing

    tracer = setup_tracing(service_name)

    try:
        from opentelemetry import context
        from opentelemetry.trace import StatusCode
        from opentelemetry.propagate import extract
    except ImportError:
        logger.info("OpenTelemetry not installed - Flask tracing disabled")
        return

    @app.before_request
    def start_span():
        from flask import request, g

        ctx = extract(carrier=dict(request.headers))
        token = context.attach(ctx)
        g.otel_token = token

        span = tracer.start_span(
            name=f"{request.method} {request.path}",
            context=ctx,
            attributes={
                "http.method": request.method,
                "http.url": request.url,
                "http.target": request.path,
                "http.host": request.host,
                "service.name": service_name,
            },
        )
        g.otel_span = span

    @app.after_request
    def end_span(response):
        from flask import g

        span = getattr(g, "otel_span", None)
        if span:
            span.set_attribute("http.status_code", response.status_code)
            if response.status_code >= 500:
                span.set_status(StatusCode.ERROR, f"HTTP {response.status_code}")
            span.end()

        token = getattr(g, "otel_token", None)
        if token:
            context.detach(token)

        return response

    @app.teardown_request
    def teardown_span(exc):
        from flask import g

        span = getattr(g, "otel_span", None)
        if span and span.is_recording():
            if exc:
                span.set_status(StatusCode.ERROR, str(exc))
                span.record_exception(exc)
            span.end()
