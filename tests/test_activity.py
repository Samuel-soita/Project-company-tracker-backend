import pytest
from app.models import User, ActivityLog, db
from datetime import datetime, timedelta, timezone
import jwt

# -----------------------------
# Helper: generate JWT token (timezone-aware)
# -----------------------------
def generate_test_token(user_id, secret_key, hours=24):
    return jwt.encode(
        {"user_id": user_id, "exp": datetime.now(timezone.utc) + timedelta(hours=hours)},
        secret_key,
        algorithm="HS256"
    )

# -----------------------------
# Helper: login as manager and set cookie
# -----------------------------
def login_as_manager(client, app, email='manager@test.com', password='adminpass'):
    # Login as seeded manager
    login = client.post('/auth/login', json={'email': email, 'password': password})
    assert login.status_code == 200, f"Manager login failed: {login.data}"

    # Extract JWT token from cookie
    cookie_header = login.headers.get('Set-Cookie', '')
    assert 'jwt=' in cookie_header, f"No JWT cookie found in response: {cookie_header}"

    # Parse the JWT token from the cookie
    jwt_start = cookie_header.find('jwt=') + 4
    jwt_end = cookie_header.find(';', jwt_start)
    if jwt_end == -1:
        jwt_token = cookie_header[jwt_start:]
    else:
        jwt_token = cookie_header[jwt_start:jwt_end]

    return jwt_token

# -----------------------------
# Test: Admin can list activities
# -----------------------------
def test_list_activities_manager(client, app):
    # Login as manager (sets cookie automatically)
    login = client.post('/auth/login', json={'email': 'manager@test.com', 'password': 'adminpass'})
    assert login.status_code == 200

    # Seed activity if none exist
    with app.app_context():
        manager_user = db.session.execute(
            db.select(User).filter_by(email='manager@test.com')
        ).scalar_one()
        if ActivityLog.query.count() == 0:
            db.session.add(ActivityLog(user_id=manager_user.id, action="Test activity"))
            db.session.commit()

    res = client.get('/activities/activities')
    assert res.status_code == 200
    data = res.json
    assert 'items' in data
    assert 'page' in data
    assert 'total_pages' in data
    assert 'total_items' in data

    if data['items']:
        activity = data['items'][0]
        for key in ['id', 'user_id', 'action', 'created_at']:
            assert key in activity

# -----------------------------
# Test: Non-manager cannot list activities
# -----------------------------
def test_list_activities_non_manager_denied(client, app):
    # Login as seeded employee (sets cookie automatically)
    login = client.post('/auth/login', json={'email': 'employee1@company.com', 'password': 'employeepass'})
    assert login.status_code == 200

    res = client.get('/activities/activities')
    assert res.status_code == 403
    assert res.json['message'] == 'You are not authorized to access this resource.'