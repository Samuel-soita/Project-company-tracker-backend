from flask import Blueprint, request, jsonify, make_response
from flask_limiter import Limiter
from flask_limiter.util import get_remote_address
from app.models import db, User
from app.utils.auth import generate_jwt
from app.utils.email_utils import send_2fa_code_email
from app.utils.error_handlers import send_error_response, send_validation_error
import random
import string
from datetime import datetime, timedelta
import logging
import os

# Rate limiter for auth routes
auth_limiter = Limiter(get_remote_address, default_limits=["10 per minute"])

auth_routes = Blueprint('auth_routes', __name__)

# -----------------------------
# Configure logger
# -----------------------------
logger = logging.getLogger(__name__)
logger.setLevel(logging.INFO)

# Temporary storage for 2FA codes (in production, use Redis or database)
two_fa_codes = {}

def generate_2fa_code():
    """Generate a random 6-digit 2FA code"""
    return ''.join(random.choices(string.digits, k=6))

# -----------------------------
# Register new user
# -----------------------------
@auth_routes.route('/auth/register', methods=['POST'])
@auth_limiter.limit("5 per hour")  # Stricter limit for registration
def register():
    data = request.get_json(silent=True) or {}

    name = data.get('name')
    email = data.get('email')
    password = data.get('password')
    role = data.get('role', 'Student')

    if not all([name, email, password]):
        return jsonify({'message': 'Name, email, and password are required'}), 400

    if User.query.filter_by(email=email).first():
        return jsonify({'message': 'Email already registered'}), 400

    user = User(name=name, email=email, role=role)
    user.set_password(password)
    db.session.add(user)
    db.session.commit()

    logger.info(f"New user registered: {email}")
    return jsonify({'message': 'User registered successfully.'}), 201

# -----------------------------
# Login endpoint
# -----------------------------
@auth_routes.route('/auth/login', methods=['POST'])
@auth_limiter.limit("5 per minute")  # Prevent brute force attacks
def login():
    # FIX: ensure data is always a dict
    data = request.get_json(silent=True) or {}

    email = data.get('email')
    password = data.get('password')

    if not all([email, password]):
        return send_validation_error('Email and password are required')

    user = User.query.filter_by(email=email).first()
    if not user or not user.check_password(password):
        return send_error_response('Invalid credentials', 401, 'INVALID_CREDENTIALS')

    # 2FA flow
    if user.two_factor_enabled:
        code = generate_2fa_code()
        expiry = datetime.now() + timedelta(minutes=10)

        two_fa_codes[user.id] = { 'code': code, 'expiry': expiry }

        try:
            send_2fa_code_email(user.email, code, user.name)
            logger.info(f"2FA code sent to {user.email}")
        except Exception as e:
            logger.error(f"Failed to send 2FA code to {user.email}: {str(e)}")
            logger.warning(f"=== DEV MODE: 2FA CODE FOR {user.email}: {code} ===")
            # Continue login instead of returning error
            pass

        return jsonify({
            'message': '2FA code sent to your email',
            'user_id': user.id,
            'two_factor_enabled': True
        }), 200

    # Normal login → generate JWT and set httpOnly cookie
    try:
        token = generate_jwt(user.id, user.role)
    except Exception as e:
        logger.error(f"JWT generation failed for user {user.id}: {str(e)}")
        return jsonify({'message': 'Login failed'}), 500

    # Create response with user data (no token in response)
    response = make_response(jsonify({
        'user': {
            'id': user.id,
            'name': user.name,
            'email': user.email,
            'role': user.role,
            'two_factor_enabled': user.two_factor_enabled,
            'class_id': user.class_id,
            'cohort_id': user.cohort_id
        }
    }), 200)

    # Set httpOnly cookie with JWT token
    is_production = os.environ.get('FLASK_ENV') == 'production' or os.environ.get('NODE_ENV') == 'production'
    response.set_cookie(
        'jwt',
        token,
        httponly=True,
        secure=is_production,
        samesite='strict',
        max_age=24 * 60 * 60  # 24 hours
    )

    return response

# -----------------------------
# Verify 2FA code
# -----------------------------
@auth_routes.route('/auth/verify-2fa', methods=['POST'])
@auth_limiter.limit("3 per minute")  # Very strict for 2FA attempts
def verify_2fa():
    data = request.get_json(silent=True) or {}

    user_id = data.get('user_id')
    code = data.get('code')

    if not all([user_id, code]):
        return send_validation_error('User ID and 2FA code are required')

    try:
        user_id = int(user_id)
    except (ValueError, TypeError):
        return send_validation_error('Invalid user ID')

    user = db.session.get(User, user_id)
    if not user or not user.two_factor_enabled:
        return send_error_response('2FA not enabled for this user', 400, '2FA_NOT_ENABLED')

    if user_id not in two_fa_codes:
        logger.warning(f"No 2FA code found for user_id: {user_id}. Available keys: {list(two_fa_codes.keys())}")
        return send_error_response('No 2FA code found. Please request a new code.', 400, '2FA_CODE_NOT_FOUND')

    stored_data = two_fa_codes[user_id]

    if datetime.now() > stored_data['expiry']:
        del two_fa_codes[user_id]
        return send_error_response('2FA code expired. Please login again.', 400, '2FA_CODE_EXPIRED')

    if code != stored_data['code']:
        return send_error_response('Invalid 2FA code', 401, 'INVALID_2FA_CODE')

    del two_fa_codes[user_id]

    try:
        token = generate_jwt(user.id, user.role)
    except Exception as e:
        logger.error(f"JWT generation failed for user {user.id}: {str(e)}")
        return jsonify({'message': '2FA verification failed'}), 500

    # Create response with user data (no token in response)
    response = make_response(jsonify({
        'user': {
            'id': user.id,
            'name': user.name,
            'email': user.email,
            'role': user.role,
            'two_factor_enabled': user.two_factor_enabled,
            'class_id': user.class_id,
            'cohort_id': user.cohort_id
        }
    }), 200)

    # Set httpOnly cookie with JWT token
    is_production = os.environ.get('FLASK_ENV') == 'production' or os.environ.get('NODE_ENV') == 'production'
    response.set_cookie(
        'jwt',
        token,
        httponly=True,
        secure=is_production,
        samesite='strict',
        max_age=24 * 60 * 60  # 24 hours
    )

    return response

# -----------------------------
# Enable 2FA
# -----------------------------
@auth_routes.route('/auth/enable-2fa', methods=['POST'])
def enable_2fa():
    data = request.get_json(silent=True) or {}
    user_id = data.get('user_id')

    if not user_id:
        return jsonify({'message': 'User ID is required'}), 400

    user = db.session.get(User, user_id)
    if not user:
        return jsonify({'message': 'User not found'}), 404

    if user.two_factor_enabled:
        return jsonify({'message': '2FA already enabled'}), 200

    user.two_factor_enabled = True
    user.two_factor_secret = 'email-based-2fa'
    db.session.commit()

    logger.info(f"2FA enabled for user {user.email}")
    return jsonify({'message': '2FA enabled successfully. You will receive a code via email when logging in.'}), 200

# -----------------------------
# Disable 2FA
# -----------------------------
@auth_routes.route('/auth/disable-2fa', methods=['POST'])
def disable_2fa():
    data = request.get_json(silent=True) or {}
    user_id = data.get('user_id')

    if not user_id:
        return jsonify({'message': 'User ID is required'}), 400

    user = db.session.get(User, user_id)
    if not user:
        return jsonify({'message': 'User not found'}), 404

    user.two_factor_enabled = False
    user.two_factor_secret = None
    db.session.commit()
    logger.info(f"2FA disabled for user {user.email}")

    return jsonify({'message': '2FA disabled'}), 200

# -----------------------------
# Logout endpoint - clear JWT cookie
# -----------------------------
@auth_routes.route('/auth/logout', methods=['POST'])
def logout():
    response = make_response(jsonify({'message': 'Logged out successfully'}), 200)

    # Clear the JWT cookie
    is_production = os.environ.get('FLASK_ENV') == 'production' or os.environ.get('NODE_ENV') == 'production'
    response.set_cookie(
        'jwt',
        '',
        httponly=True,
        secure=is_production,
        samesite='strict',
        max_age=0  # Expire immediately
    )

    logger.info("User logged out successfully")
    return response
