import logging
import uuid
from contextlib import asynccontextmanager

from fastapi import FastAPI, Request, Response
from fastapi.responses import JSONResponse

from app.auth import auth_middleware
from app.config import settings
from app.rate_limiter import check_rate_limit, close_redis, init_redis
from app.service_proxy import (
    close_http_client,
    get_circuit_breaker_status,
    init_http_client,
    proxy_request,
)

# Import shared logging from project-level shared library
import sys
import os

sys.path.insert(0, os.path.join(os.path.dirname(__file__), "..", ".."))
from shared.logging_config import setup_logging
from shared.metrics_fastapi import PrometheusMiddleware
from shared.tracing_fastapi import TracingMiddleware

setup_logging(settings.SERVICE_NAME, settings.LOG_LEVEL)
logger = logging.getLogger(__name__)

# ---- Route prefix -> service name mapping ----
ROUTE_MAP = {
    "/products": "products",
    "/orders": "orders",
    "/inventory": "inventory",
}


@asynccontextmanager
async def lifespan(app: FastAPI):
    """Startup / shutdown lifecycle."""
    await init_redis()
    await init_http_client()
    logger.info("Gateway started")
    yield
    await close_redis()
    await close_http_client()
    logger.info("Gateway stopped")


app = FastAPI(
    title="NexuShop API Gateway",
    description="Unified entry point with JWT auth, rate limiting, and circuit breakers",
    version="1.0.0",
    lifespan=lifespan,
)

app.add_middleware(PrometheusMiddleware, service_name=settings.SERVICE_NAME)
app.add_middleware(TracingMiddleware, service_name=settings.SERVICE_NAME)


# ---- Middleware ----


@app.middleware("http")
async def gateway_middleware(request: Request, call_next):
    """Pipeline: correlation ID -> auth -> rate limit -> proxy."""
    # 1. Correlation ID
    correlation_id = request.headers.get("X-Correlation-ID", str(uuid.uuid4()))
    request.state.correlation_id = correlation_id

    # 2. Authentication
    try:
        user_claims = await auth_middleware(request)
        request.state.user = user_claims
    except Exception as exc:
        if hasattr(exc, "status_code"):
            return JSONResponse(
                status_code=exc.status_code,
                content={"error": exc.detail},
                headers={"X-Correlation-ID": correlation_id},
            )
        raise

    # 3. Rate limiting
    try:
        await check_rate_limit(request)
    except Exception as exc:
        if hasattr(exc, "status_code"):
            return JSONResponse(
                status_code=exc.status_code,
                content={"error": exc.detail},
                headers={"X-Correlation-ID": correlation_id},
            )
        raise

    # 4. Continue to route handler
    response = await call_next(request)
    response.headers["X-Correlation-ID"] = correlation_id
    return response


# ---- Gateway-local endpoints ----


@app.get("/health")
async def health():
    return {"status": "healthy", "service": settings.SERVICE_NAME}


@app.get("/ready")
async def ready():
    return {
        "status": "ready",
        "service": settings.SERVICE_NAME,
        "circuit_breakers": get_circuit_breaker_status(),
    }


@app.post("/auth/login")
async def login(request: Request):
    """Issue a JWT token (demo endpoint - no real user store)."""
    from app.auth import create_token

    body = await request.json()
    email = body.get("email")
    if not email:
        return JSONResponse(status_code=400, content={"error": "email is required"})
    user_id = body.get("user_id", str(uuid.uuid4()))
    role = body.get("role", "customer")
    token = create_token(user_id, email, role)
    return {"access_token": token, "token_type": "bearer"}


@app.get("/auth/me")
async def me(request: Request):
    """Return the current user's claims from their JWT."""
    user = getattr(request.state, "user", None)
    if not user:
        return JSONResponse(status_code=401, content={"error": "Not authenticated"})
    return user


@app.get("/gateway/circuits")
async def circuits():
    """Expose circuit breaker states for monitoring."""
    return get_circuit_breaker_status()


# ---- Catch-all proxy routes ----


@app.api_route(
    "/{path:path}",
    methods=["GET", "POST", "PUT", "PATCH", "DELETE"],
)
async def proxy(request: Request, path: str):
    """Forward requests to downstream microservices."""
    # Determine target service
    full_path = f"/{path}"
    service_name = None
    for prefix, svc in ROUTE_MAP.items():
        if full_path.startswith(prefix):
            service_name = svc
            break

    if service_name is None:
        return JSONResponse(status_code=404, content={"error": "Route not found"})

    body = await request.body()
    correlation_id = getattr(request.state, "correlation_id", str(uuid.uuid4()))

    response = await proxy_request(
        service_name=service_name,
        path=full_path,
        method=request.method,
        headers=dict(request.headers),
        body=body if body else None,
        query_string=str(request.query_params),
        correlation_id=correlation_id,
    )

    if response is None:
        return JSONResponse(status_code=404, content={"error": "Route not found"})

    return Response(
        content=response.content,
        status_code=response.status_code,
        headers=dict(response.headers),
        media_type=response.headers.get("content-type"),
    )
