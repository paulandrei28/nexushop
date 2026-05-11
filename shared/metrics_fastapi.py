"""FastAPI middleware for Prometheus request metrics."""

import time
from starlette.middleware.base import BaseHTTPMiddleware
from starlette.requests import Request
from starlette.responses import Response
from shared.metrics import (
    REQUEST_COUNT,
    REQUEST_LATENCY,
    REQUESTS_IN_PROGRESS,
    SERVICE_INFO,
    get_metrics,
    get_metrics_content_type,
)


class PrometheusMiddleware(BaseHTTPMiddleware):
    """Middleware that records request metrics for Prometheus."""

    def __init__(self, app, service_name: str):
        super().__init__(app)
        self.service_name = service_name
        SERVICE_INFO.info({"name": service_name, "framework": "fastapi"})

    async def dispatch(self, request: Request, call_next):
        if request.url.path == "/metrics":
            return Response(
                content=get_metrics(),
                media_type=get_metrics_content_type(),
            )

        REQUESTS_IN_PROGRESS.labels(service=self.service_name).inc()
        start = time.time()

        response = await call_next(request)

        latency = time.time() - start
        REQUESTS_IN_PROGRESS.labels(service=self.service_name).dec()

        endpoint = _normalize_path(request.url.path)
        REQUEST_COUNT.labels(
            service=self.service_name,
            method=request.method,
            endpoint=endpoint,
            status_code=response.status_code,
        ).inc()
        REQUEST_LATENCY.labels(
            service=self.service_name,
            method=request.method,
            endpoint=endpoint,
        ).observe(latency)

        return response


def _normalize_path(path: str) -> str:
    """Normalize path to reduce cardinality (replace IDs with {id})."""
    parts = path.split("/")
    normalized = []
    for p in parts:
        if not p:
            normalized.append(p)
        elif len(p) >= 20 or p.isdigit() or (len(p) == 36 and p.count("-") == 4):
            normalized.append("{id}")
        else:
            normalized.append(p)
    return "/".join(normalized)
