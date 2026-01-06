import jwt
import os
import logging
from datetime import datetime, timedelta, timezone
from functools import wraps
from flask import request, current_app, jsonify
from app.models import User
from app.utils.error_handlers import send_unauthorized_error
from app import db

# -----------------------------
# Configure logger
# -----------------------------
logger = logging.getLogger(__name__)
logger.setLevel(logging.INFO)

# -----------------------------
# Generate JWT Access Token
# -----------------------------
def generate_jwt(user_id, role, expires_hours=1):
    """
    Generates a JWT access token with user_id and role.
    Default expiration: 1 hour
    """
    secret_key = current_app.config.get("SECRET_KEY") or os.environ.get("SECRET_KEY")
    if not secret_key:
        raise RuntimeError("SECRET_KEY not configured in environment or Flask config")

    payload = {
        "user_id": user_id,
        "role": role,
        # Use timezone-aware datetime to avoid DeprecationWarning
        "exp": datetime.now(timezone.utc) + timedelta(hours=expires_hours)
    }
    token = jwt.encode(payload, secret_key, algorithm="HS256")
    return token

# -----------------------------
# Token verification decorator
# -----------------------------
def token_required(f):
    """
    Decorator to protect routes requiring JWT authentication.
    Adds 'current_user' as the first argument to the route.
    Reads JWT from httpOnly cookie instead of Authorization header.
    """
    @wraps(f)
    def decorated(*args, **kwargs):
        token = None

        # JWT expected in httpOnly cookie
        token = request.cookies.get('jwt')

        if not token:
            return send_unauthorized_error("Authentication required. Please log in.")

        try:
            secret_key = current_app.config.get("SECRET_KEY") or os.environ.get("SECRET_KEY")
            data = jwt.decode(token, secret_key, algorithms=["HS256"])
            # Use SQLAlchemy 2.x Session.get() instead of legacy Query.get()
            current_user = db.session.get(User, data["user_id"])
            if not current_user:
                raise Exception("User not found")
        except jwt.ExpiredSignatureError:
            return send_unauthorized_error("Token has expired. Please log in again.")
        except jwt.InvalidTokenError:
            return send_unauthorized_error("Invalid token. Please log in again.")
        except Exception as e:
            logger.error(f"JWT verification error: {str(e)}")
            return send_unauthorized_error("Token verification failed.")

        return f(current_user, *args, **kwargs)

    return decorated

# -----------------------------
# Role verification decorator
# -----------------------------
def role_required(allowed_roles):
    """
    Decorator to restrict access based on user roles.
    Example: @role_required(['Admin', 'Moderator'])
    """
    def decorator(f):
        @wraps(f)
        def wrapper(current_user, *args, **kwargs):
            if current_user.role not in allowed_roles:
                return jsonify({"message": "You are not authorized to access this resource."}), 403
            return f(current_user, *args, **kwargs)
        return wrapper
    return decorator
