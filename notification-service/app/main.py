import sys
import os
import logging

from fastapi import FastAPI
from contextlib import asynccontextmanager

# Add paths for shared library
sys.path.insert(0, os.path.join(os.path.dirname(__file__), ".."))
sys.path.insert(0, os.path.join(os.path.dirname(__file__), "..", ".."))

from app.config import settings
from app.events import start_consumer
from shared.logging_config import setup_logging
from shared.metrics_fastapi import PrometheusMiddleware
from shared.tracing_fastapi import TracingMiddleware

logger = logging.getLogger(__name__)

# Initialize logging
setup_logging(service_name=settings.SERVICE_NAME, level=settings.LOG_LEVEL)


@asynccontextmanager
async def lifespan(app: FastAPI):
    # Startup
    logger.info("Notification service starting up...")
    try:
        start_consumer()
    except Exception:
        logger.warning("Could not start RabbitMQ consumer (will retry on restart)")
    yield
    # Shutdown
    logger.info("Notification service shutting down...")


app = FastAPI(
    title="Notification Service",
    description="Event-driven email notifications",
    version="1.0.0",
    lifespan=lifespan,
)


@app.get("/health")
def health():
    return {"status": "ok", "service": settings.SERVICE_NAME}


@app.get("/ready")
def ready():
    return {"status": "ok", "service": settings.SERVICE_NAME}


app.add_middleware(PrometheusMiddleware, service_name=settings.SERVICE_NAME)
app.add_middleware(TracingMiddleware, service_name=settings.SERVICE_NAME)
