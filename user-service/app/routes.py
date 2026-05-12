import logging
import re
import time

import jwt
from flask import Blueprint, jsonify, request

from app.config import Config
from app.extensions import db
from app.models import User

logger = logging.getLogger(__name__)

auth_bp = Blueprint("auth", __name__)

EMAIL_REGEX = re.compile(r"^[a-zA-Z0-9._%+\-]+@[a-zA-Z0-9.\-]+\.[a-zA-Z]{2,}$")
MIN_PASSWORD_LENGTH = 8


def _create_token(user):
    """Create a JWT for the given user."""
    now = time.time()
    payload = {
        "sub": user.id,
        "email": user.email,
        "name": user.name,
        "role": user.role,
        "iat": int(now),
        "exp": int(now + Config.JWT_EXPIRY_MINUTES * 60),
    }
    return jwt.encode(payload, Config.JWT_SECRET, algorithm=Config.JWT_ALGORITHM)


def _validate_email(email):
    if not email or not EMAIL_REGEX.match(email):
        return False
    return True


def _validate_password(password):
    if not password or len(password) < MIN_PASSWORD_LENGTH:
        return False
    return True


@auth_bp.route("/auth/register", methods=["POST"])
def register():
    """Register a new user account."""
    data = request.get_json(silent=True)
    if not data:
        return jsonify({"error": "Request body is required"}), 400

    email = (data.get("email") or "").strip().lower()
    password = data.get("password") or ""
    name = (data.get("name") or "").strip()

    if not _validate_email(email):
        return jsonify({"error": "A valid email address is required"}), 400

    if not _validate_password(password):
        return (
            jsonify({"error": "Password must be at least 8 characters long"}),
            400,
        )

    if not name:
        return jsonify({"error": "Name is required"}), 400

    existing = db.session.query(User).filter(User.email == email).first()
    if existing:
        return jsonify({"error": "An account with this email already exists"}), 409

    user = User(email=email, name=name)
    user.set_password(password)
    db.session.add(user)
    db.session.commit()

    token = _create_token(user)
    logger.info("User registered: %s", email)

    return (
        jsonify(
            {
                "access_token": token,
                "token_type": "bearer",
                "user": user.to_dict(),
            }
        ),
        201,
    )


@auth_bp.route("/auth/login", methods=["POST"])
def login():
    """Authenticate a user and return a JWT."""
    data = request.get_json(silent=True)
    if not data:
        return jsonify({"error": "Request body is required"}), 400

    email = (data.get("email") or "").strip().lower()
    password = data.get("password") or ""

    if not email or not password:
        return jsonify({"error": "Email and password are required"}), 400

    user = db.session.query(User).filter(User.email == email).first()
    if not user or not user.verify_password(password):
        return jsonify({"error": "Invalid email or password"}), 401

    if not user.is_active:
        return jsonify({"error": "Account is deactivated"}), 403

    token = _create_token(user)
    logger.info("User logged in: %s", email)

    return jsonify(
        {
            "access_token": token,
            "token_type": "bearer",
            "user": user.to_dict(),
        }
    )


@auth_bp.route("/auth/me", methods=["GET"])
def me():
    """Return the current user profile from JWT claims."""
    auth_header = request.headers.get("Authorization", "")
    if not auth_header.startswith("Bearer "):
        return jsonify({"error": "Missing or invalid Authorization header"}), 401

    token = auth_header.split(" ", 1)[1]
    try:
        claims = jwt.decode(token, Config.JWT_SECRET, algorithms=[Config.JWT_ALGORITHM])
    except jwt.ExpiredSignatureError:
        return jsonify({"error": "Token has expired"}), 401
    except jwt.InvalidTokenError:
        return jsonify({"error": "Invalid token"}), 401

    user = db.session.query(User).filter(User.id == claims["sub"]).first()
    if not user:
        return jsonify({"error": "User not found"}), 404

    return jsonify(user.to_dict())
