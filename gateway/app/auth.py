import logging
import time
from typing import Optional

import jwt
from fastapi import HTTPException, Request
from fastapi.security import HTTPAuthorizationCredentials, HTTPBearer

from app.config import settings

logger = logging.getLogger(__name__)

security = HTTPBearer(auto_error=False)

# Endpoints that don't require authentication
PUBLIC_PATHS = frozenset(
    {
        "/health",
        "/ready",
        "/auth/register",
        "/auth/login",
        "/docs",
        "/openapi.json",
        "/redoc",
        "/gateway/circuits",
        "/metrics",
    }
)

# Prefix-based public paths (read-only product browsing)
PUBLIC_PREFIXES = ("/products",)

# Specific paths that are public regardless of method
PUBLIC_PATH_METHOD = {
    "/inventory/batch": ("POST",),
}


def create_token(user_id: str, email: str, role: str = "customer") -> str:
    """Create a JWT token for a user."""
    now = time.time()
    payload = {
        "sub": user_id,
        "email": email,
        "role": role,
        "iat": int(now),
        "exp": int(now + settings.JWT_EXPIRY_MINUTES * 60),
    }
    return jwt.encode(payload, settings.JWT_SECRET, algorithm=settings.JWT_ALGORITHM)


def decode_token(token: str) -> dict:
    """Decode and validate a JWT token."""
    try:
        return jwt.decode(
            token,
            settings.JWT_SECRET,
            algorithms=[settings.JWT_ALGORITHM],
        )
    except jwt.ExpiredSignatureError:
        raise HTTPException(status_code=401, detail="Token has expired")
    except jwt.InvalidTokenError:
        raise HTTPException(status_code=401, detail="Invalid token")


def _is_public_path(path: str, method: str) -> bool:
    """Check if the request path is publicly accessible."""
    if path in PUBLIC_PATHS:
        return True
    # Allow GET requests to product browsing endpoints
    if method == "GET" and any(path.startswith(p) for p in PUBLIC_PREFIXES):
        return True
    # Allow specific method+path combos (e.g. POST /inventory/batch)
    if path in PUBLIC_PATH_METHOD and method in PUBLIC_PATH_METHOD[path]:
        return True
    # Allow GET on individual inventory items (for product detail page)
    if method == "GET" and path.startswith("/inventory/"):
        return True
    return False


async def auth_middleware(request: Request) -> Optional[dict]:
    """Authenticate request via JWT. Returns user claims or None for public paths."""
    if _is_public_path(request.url.path, request.method):
        return None

    auth_header = request.headers.get("Authorization")
    if not auth_header or not auth_header.startswith("Bearer "):
        raise HTTPException(
            status_code=401, detail="Missing or invalid Authorization header"
        )

    token = auth_header.split(" ", 1)[1]
    claims = decode_token(token)
    return claims
