import logging
import time

import redis.asyncio as aioredis
from fastapi import HTTPException, Request

from app.config import settings

logger = logging.getLogger(__name__)

_redis_pool: aioredis.Redis = None


async def init_redis():
    """Initialize the Redis connection pool."""
    global _redis_pool
    _redis_pool = aioredis.from_url(
        settings.REDIS_URL,
        decode_responses=True,
        socket_connect_timeout=5,
    )
    try:
        await _redis_pool.ping()
        logger.info("Connected to Redis for rate limiting")
    except Exception:
        logger.warning("Redis unavailable - rate limiting disabled")
        _redis_pool = None


async def close_redis():
    """Close the Redis connection pool."""
    global _redis_pool
    if _redis_pool:
        await _redis_pool.close()
        _redis_pool = None


def _get_client_key(request: Request) -> str:
    """Get a rate-limit key for the client (IP-based or token-based)."""
    # Use user ID from JWT if available, otherwise use IP
    user_claims = getattr(request.state, "user", None)
    if user_claims and isinstance(user_claims, dict):
        return f"rate_limit:user:{user_claims.get('sub', 'anon')}"
    client_ip = request.client.host if request.client else "unknown"
    return f"rate_limit:ip:{client_ip}"


async def check_rate_limit(request: Request):
    """Check if the request exceeds the rate limit using sliding window."""
    if _redis_pool is None:
        return  # Gracefully skip if Redis is down

    key = _get_client_key(request)
    window = settings.RATE_LIMIT_WINDOW
    max_requests = settings.RATE_LIMIT_REQUESTS

    try:
        now = time.time()
        pipe = _redis_pool.pipeline()
        # Remove old entries outside the window
        pipe.zremrangebyscore(key, 0, now - window)
        # Add current request
        pipe.zadd(key, {str(now): now})
        # Count requests in window
        pipe.zcard(key)
        # Set expiry on the key
        pipe.expire(key, window)
        results = await pipe.execute()

        request_count = results[2]

        if request_count > max_requests:
            logger.warning(
                "Rate limit exceeded for %s: %d/%d",
                key,
                request_count,
                max_requests,
            )
            raise HTTPException(
                status_code=429,
                detail=f"Rate limit exceeded. Max {max_requests} requests per {window}s",
            )
    except HTTPException:
        raise
    except Exception as exc:
        # If Redis fails, allow the request through (fail-open)
        logger.warning("Rate limiter error (allowing request): %s", str(exc))
