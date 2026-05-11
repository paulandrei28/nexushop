"""Prometheus metrics helpers for microservices."""

import time
from prometheus_client import (
    Counter,
    Histogram,
    Gauge,
    Info,
    generate_latest,
    CONTENT_TYPE_LATEST,
    CollectorRegistry,
    REGISTRY,
)

# ---- Common metrics ----

REQUEST_COUNT = Counter(
    "http_requests_total",
    "Total HTTP requests",
    ["service", "method", "endpoint", "status_code"],
)

REQUEST_LATENCY = Histogram(
    "http_request_duration_seconds",
    "HTTP request latency in seconds",
    ["service", "method", "endpoint"],
    buckets=(0.005, 0.01, 0.025, 0.05, 0.1, 0.25, 0.5, 1.0, 2.5, 5.0, 10.0),
)

REQUESTS_IN_PROGRESS = Gauge(
    "http_requests_in_progress",
    "Number of HTTP requests currently being processed",
    ["service"],
)

SERVICE_INFO = Info("service", "Service information")

# ---- Event / messaging metrics ----

EVENTS_PUBLISHED = Counter(
    "events_published_total",
    "Total events published to message broker",
    ["service", "exchange", "routing_key"],
)

EVENTS_CONSUMED = Counter(
    "events_consumed_total",
    "Total events consumed from message broker",
    ["service", "queue", "status"],
)

# ---- Circuit breaker metrics (gateway) ----

CIRCUIT_BREAKER_STATE = Gauge(
    "circuit_breaker_state",
    "Circuit breaker state (0=closed, 1=open, 2=half-open)",
    ["service", "target_service"],
)

CIRCUIT_BREAKER_FAILURES = Counter(
    "circuit_breaker_failures_total",
    "Total circuit breaker recorded failures",
    ["service", "target_service"],
)

# ---- Database metrics ----

DB_QUERY_DURATION = Histogram(
    "db_query_duration_seconds",
    "Database query duration in seconds",
    ["service", "operation"],
    buckets=(0.001, 0.005, 0.01, 0.025, 0.05, 0.1, 0.25, 0.5, 1.0),
)


def get_metrics() -> bytes:
    """Generate Prometheus metrics output."""
    return generate_latest(REGISTRY)


def get_metrics_content_type() -> str:
    """Return the Prometheus content type."""
    return CONTENT_TYPE_LATEST
