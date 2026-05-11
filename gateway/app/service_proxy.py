import logging
import time
import threading
from enum import Enum
from typing import Optional

import httpx
from tenacity import (
    retry,
    retry_if_exception_type,
    stop_after_attempt,
    wait_exponential,
)

from app.config import settings

logger = logging.getLogger(__name__)

# ---- Async-compatible Circuit Breaker ----

CIRCUIT_ERRORS = (httpx.ConnectError, httpx.ConnectTimeout, httpx.ReadTimeout)


class CircuitState(str, Enum):
    CLOSED = "closed"
    OPEN = "open"
    HALF_OPEN = "half-open"


class AsyncCircuitBreaker:
    """Async-compatible circuit breaker (pybreaker.call_async needs Tornado)."""

    def __init__(self, name: str, fail_max: int = 5, reset_timeout: int = 30):
        self.name = name
        self.fail_max = fail_max
        self.reset_timeout = reset_timeout
        self._fail_counter = 0
        self._state = CircuitState.CLOSED
        self._opened_at: float = 0
        self._lock = threading.Lock()

    @property
    def state(self) -> str:
        if self._state == CircuitState.OPEN:
            if time.time() - self._opened_at >= self.reset_timeout:
                self._state = CircuitState.HALF_OPEN
        return self._state.value

    @property
    def fail_counter(self) -> int:
        return self._fail_counter

    def record_success(self):
        with self._lock:
            self._fail_counter = 0
            if self._state != CircuitState.CLOSED:
                logger.warning(
                    "Circuit breaker '%s': %s -> closed", self.name, self._state.value
                )
                self._state = CircuitState.CLOSED

    def record_failure(self):
        with self._lock:
            self._fail_counter += 1
            if self._fail_counter >= self.fail_max:
                if self._state != CircuitState.OPEN:
                    logger.warning(
                        "Circuit breaker '%s': %s -> open (failures=%d/%d)",
                        self.name,
                        self._state.value,
                        self._fail_counter,
                        self.fail_max,
                    )
                self._state = CircuitState.OPEN
                self._opened_at = time.time()

    def is_call_permitted(self) -> bool:
        state = self.state  # triggers half-open check
        if state == CircuitState.CLOSED.value:
            return True
        if state == CircuitState.HALF_OPEN.value:
            return True  # allow one probe request
        return False


# ---- Circuit breaker instances ----

product_cb = AsyncCircuitBreaker("product-service")
order_cb = AsyncCircuitBreaker("order-service")
inventory_cb = AsyncCircuitBreaker("inventory-service")

SERVICE_MAP = {
    "products": (settings.PRODUCT_SERVICE_URL, product_cb),
    "orders": (settings.ORDER_SERVICE_URL, order_cb),
    "inventory": (settings.INVENTORY_SERVICE_URL, inventory_cb),
}

# Shared async HTTP client
_http_client: Optional[httpx.AsyncClient] = None


async def init_http_client():
    global _http_client
    _http_client = httpx.AsyncClient(timeout=httpx.Timeout(10.0, connect=5.0))


async def close_http_client():
    global _http_client
    if _http_client:
        await _http_client.aclose()
        _http_client = None


@retry(
    stop=stop_after_attempt(3),
    wait=wait_exponential(multiplier=0.5, min=0.5, max=4),
    retry=retry_if_exception_type((httpx.ConnectError, httpx.ConnectTimeout)),
    reraise=True,
)
async def _forward_request(
    base_url: str,
    path: str,
    method: str,
    headers: dict,
    body: Optional[bytes],
    query_string: str,
) -> httpx.Response:
    """Forward a request to a downstream service with retry."""
    url = f"{base_url}{path}"
    if query_string:
        url = f"{url}?{query_string}"

    return await _http_client.request(
        method=method,
        url=url,
        headers=headers,
        content=body,
    )


async def proxy_request(
    service_name: str,
    path: str,
    method: str,
    headers: dict,
    body: Optional[bytes],
    query_string: str,
    correlation_id: str,
) -> httpx.Response:
    """Route a request through circuit breaker + retry to a downstream service."""
    if service_name not in SERVICE_MAP:
        return None

    base_url, cb = SERVICE_MAP[service_name]

    # Check circuit breaker state
    if not cb.is_call_permitted():
        logger.error("Circuit OPEN for %s - rejecting request", service_name)
        return _service_unavailable_response(service_name)

    # Inject correlation ID into forwarded headers
    forward_headers = {
        k: v
        for k, v in headers.items()
        if k.lower()
        not in ("host", "content-length", "transfer-encoding", "connection")
    }
    forward_headers["X-Correlation-ID"] = correlation_id

    try:
        response = await _forward_request(
            base_url=base_url,
            path=path,
            method=method,
            headers=forward_headers,
            body=body,
            query_string=query_string,
        )
        cb.record_success()
        return response
    except (httpx.ConnectError, httpx.ConnectTimeout):
        cb.record_failure()
        logger.error(
            "Service %s unreachable (failures=%d/%d)",
            service_name,
            cb.fail_counter,
            cb.fail_max,
        )
        return _service_unavailable_response(service_name)
    except httpx.TimeoutException:
        cb.record_failure()
        logger.error("Service %s request timed out", service_name)
        return _gateway_timeout_response(service_name)


def _service_unavailable_response(service_name: str) -> httpx.Response:
    """Create a 503 response when a service is unavailable."""
    return httpx.Response(
        status_code=503,
        json={
            "error": "Service temporarily unavailable",
            "service": service_name,
            "detail": "Circuit breaker is open or service unreachable. Retrying shortly.",
        },
    )


def _gateway_timeout_response(service_name: str) -> httpx.Response:
    """Create a 504 response when a service times out."""
    return httpx.Response(
        status_code=504,
        json={
            "error": "Gateway timeout",
            "service": service_name,
            "detail": "Downstream service did not respond in time.",
        },
    )


def get_circuit_breaker_status() -> dict:
    """Return the status of all circuit breakers."""
    return {
        name: {
            "state": cb.state,
            "fail_count": cb.fail_counter,
            "fail_max": cb.fail_max,
            "reset_timeout": cb.reset_timeout,
        }
        for name, (_, cb) in SERVICE_MAP.items()
    }
