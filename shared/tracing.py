"""OpenTelemetry tracing setup for microservices."""

import os
import logging

logger = logging.getLogger(__name__)

_initialized = False
_noop = False


def setup_tracing(service_name: str):
    """Initialize OpenTelemetry tracing with OTLP exporter to Jaeger.

    Falls back to a no-op tracer if dependencies are missing or Jaeger is unavailable.
    """
    global _initialized, _noop
    if _initialized or _noop:
        return _get_tracer(service_name)

    otlp_endpoint = os.environ.get("OTEL_EXPORTER_OTLP_ENDPOINT", "")
    if not otlp_endpoint:
        logger.info("OTEL_EXPORTER_OTLP_ENDPOINT not set - tracing disabled")
        _noop = True
        return _get_tracer(service_name)

    try:
        from opentelemetry import trace
        from opentelemetry.sdk.trace import TracerProvider
        from opentelemetry.sdk.trace.export import BatchSpanProcessor
        from opentelemetry.sdk.resources import Resource, SERVICE_NAME
        from opentelemetry.exporter.otlp.proto.grpc.trace_exporter import (
            OTLPSpanExporter,
        )

        resource = Resource.create({SERVICE_NAME: service_name})
        provider = TracerProvider(resource=resource)
        exporter = OTLPSpanExporter(endpoint=otlp_endpoint, insecure=True)
        processor = BatchSpanProcessor(exporter)
        provider.add_span_processor(processor)
        trace.set_tracer_provider(provider)
        _initialized = True
        logger.info("OpenTelemetry tracing configured (endpoint=%s)", otlp_endpoint)
        return trace.get_tracer(service_name)
    except Exception as exc:
        logger.warning("Failed to configure tracing (disabled): %s", exc)
        _noop = True
        return _get_tracer(service_name)


def _get_tracer(service_name: str):
    """Get a tracer - real or no-op."""
    try:
        from opentelemetry import trace

        return trace.get_tracer(service_name)
    except ImportError:
        return _NoOpTracer()


def get_tracer(service_name: str):
    """Get an OpenTelemetry tracer."""
    return _get_tracer(service_name)


class _NoOpTracer:
    """Minimal no-op tracer for when OTel is not available."""

    def start_span(self, *args, **kwargs):
        return _NoOpSpan()


class _NoOpSpan:
    def __enter__(self):
        return self

    def __exit__(self, *args):
        pass

    def set_attribute(self, *args, **kwargs):
        pass

    def set_status(self, *args, **kwargs):
        pass

    def record_exception(self, *args, **kwargs):
        pass

    def end(self):
        pass

    def is_recording(self):
        return False
