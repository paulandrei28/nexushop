import logging
from functools import wraps
from typing import Any, Callable

import pybreaker

logger = logging.getLogger(__name__)

# Default settings: open after 5 failures, stay open for 30 seconds
DEFAULT_FAIL_MAX = 5
DEFAULT_RESET_TIMEOUT = 30


def create_circuit_breaker(
    name: str,
    fail_max: int = DEFAULT_FAIL_MAX,
    reset_timeout: int = DEFAULT_RESET_TIMEOUT,
) -> pybreaker.CircuitBreaker:
    """Create a circuit breaker with logging listeners."""

    class LogListener(pybreaker.CircuitBreakerListener):
        def state_change(self, cb, old_state, new_state):
            logger.warning(
                "Circuit breaker '%s' state changed: %s -> %s",
                cb.name,
                old_state.name,
                new_state.name,
            )

        def failure(self, cb, exc):
            logger.warning(
                "Circuit breaker '%s' recorded failure: %s",
                cb.name,
                str(exc),
            )

    return pybreaker.CircuitBreaker(
        name=name,
        fail_max=fail_max,
        reset_timeout=reset_timeout,
        listeners=[LogListener()],
    )


def with_fallback(fallback_value: Any):
    """Decorator that returns a fallback value when circuit is open."""

    def decorator(func: Callable) -> Callable:
        @wraps(func)
        def wrapper(*args, **kwargs):
            try:
                return func(*args, **kwargs)
            except pybreaker.CircuitBreakerError:
                logger.warning(
                    "Circuit open for %s, returning fallback", func.__name__
                )
                if callable(fallback_value):
                    return fallback_value()
                return fallback_value

        return wrapper

    return decorator
