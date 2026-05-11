import sys
import os
import logging

from fastapi import FastAPI
from contextlib import asynccontextmanager

# Add paths for shared library
sys.path.insert(0, os.path.join(os.path.dirname(__file__), ".."))
sys.path.insert(0, os.path.join(os.path.dirname(__file__), "..", ".."))

from app.config import settings
from app.database import init_db
from app.routes import router as orders_router
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
    logger.info("Order service starting up...")
    init_db()
    try:
        start_consumer()
    except Exception:
        logger.warning("Could not start RabbitMQ consumer (will retry on restart)")
    yield
    # Shutdown
    logger.info("Order service shutting down...")


app = FastAPI(
    title="Order Service",
    description="Order management with saga pattern",
    version="1.0.0",
    lifespan=lifespan,
)

app.include_router(orders_router)
app.add_middleware(PrometheusMiddleware, service_name=settings.SERVICE_NAME)
app.add_middleware(TracingMiddleware, service_name=settings.SERVICE_NAME)


@app.get("/health")
def health():
    return {"status": "ok", "service": settings.SERVICE_NAME}


@app.get("/ready")
def ready():
    from app.database import engine
    from sqlalchemy import text

    checks = {}
    try:
        with engine.connect() as conn:
            conn.execute(text("SELECT 1"))
        checks["database"] = "ok"
    except Exception as e:
        checks["database"] = str(e)

    all_ok = all(v == "ok" for v in checks.values())
    return {
        "status": "ok" if all_ok else "degraded",
        "service": settings.SERVICE_NAME,
        "checks": checks,
    }
