"""FastAPI middleware for OpenTelemetry tracing."""

import logging
from starlette.middleware.base import BaseHTTPMiddleware
from starlette.requests import Request

logger = logging.getLogger(__name__)

try:
    from opentelemetry import context as otel_context
    from opentelemetry.trace import StatusCode
    from opentelemetry.propagate import extract

    _HAS_OTEL = True
except ImportError:
    _HAS_OTEL = False


class TracingMiddleware(BaseHTTPMiddleware):
    """Middleware that creates OpenTelemetry spans for each request."""

    def __init__(self, app, service_name: str):
        super().__init__(app)
        self.service_name = service_name
        from shared.tracing import setup_tracing

        self.tracer = setup_tracing(service_name)

    async def dispatch(self, request: Request, call_next):
        # Skip tracing for metrics/health endpoints or if OTel unavailable
        if request.url.path in ("/metrics", "/health", "/ready") or not _HAS_OTEL:
            return await call_next(request)

        ctx = extract(carrier=dict(request.headers))
        token = otel_context.attach(ctx)

        span = self.tracer.start_span(
            name=f"{request.method} {request.url.path}",
            context=ctx,
            attributes={
                "http.method": request.method,
                "http.url": str(request.url),
                "http.target": request.url.path,
                "http.host": request.headers.get("host", ""),
                "service.name": self.service_name,
            },
        )

        try:
            response = await call_next(request)
            span.set_attribute("http.status_code", response.status_code)
            if response.status_code >= 500:
                span.set_status(StatusCode.ERROR, f"HTTP {response.status_code}")
            return response
        except Exception as exc:
            span.set_status(StatusCode.ERROR, str(exc))
            span.record_exception(exc)
            raise
        finally:
            span.end()
            otel_context.detach(token)
