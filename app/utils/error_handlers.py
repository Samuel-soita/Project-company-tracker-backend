from flask import jsonify, current_app
from datetime import datetime, timezone
import logging

logger = logging.getLogger(__name__)

# -----------------------------
# Structured Error Response Utility
# -----------------------------
def send_error_response(message, status_code=500, error_code=None, retry_after=None):
    """
    Send a structured error response with consistent format.

    Args:
        message (str): Human-readable error message
        status_code (int): HTTP status code
        error_code (str): Machine-readable error code for frontend handling
        retry_after (int): Seconds to wait before retrying (for rate limiting)

    Returns:
        Flask response object
    """
    response_data = {
        "success": False,
        "message": message,
        "timestamp": datetime.now(timezone.utc).isoformat(),
    }

    if error_code:
        response_data["error_code"] = error_code

    if retry_after:
        response_data["retry_after"] = retry_after

    # Log error for monitoring
    if status_code >= 500:
        logger.error(f"Server error ({status_code}): {message}")
    elif status_code >= 400:
        logger.warning(f"Client error ({status_code}): {message}")

    response = jsonify(response_data)
    response.status_code = status_code
    return response

# -----------------------------
# Specific Error Types
# -----------------------------
def send_validation_error(message, field_errors=None):
    """Send validation error response"""
    response_data = {
        "success": False,
        "message": message,
        "timestamp": datetime.now(timezone.utc).isoformat(),
        "error_code": "VALIDATION_ERROR"
    }

    if field_errors:
        response_data["field_errors"] = field_errors

    logger.warning(f"Validation error: {message}")
    response = jsonify(response_data)
    response.status_code = 400
    return response

def send_rate_limit_error(retry_after):
    """Send rate limit exceeded error"""
    return send_error_response(
        "Too many requests. Please try again later.",
        429,
        "RATE_LIMIT_EXCEEDED",
        retry_after
    )

def send_unauthorized_error(message="Authentication required"):
    """Send unauthorized error"""
    return send_error_response(message, 401, "UNAUTHORIZED")

def send_forbidden_error(message="Access denied"):
    """Send forbidden error"""
    return send_error_response(message, 403, "FORBIDDEN")

def send_not_found_error(resource_type="Resource"):
    """Send not found error"""
    return send_error_response(f"{resource_type} not found", 404, "NOT_FOUND")