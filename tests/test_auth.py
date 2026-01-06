import pytest
from app.models import User, db

def test_login_seeded_users(client):
    # Login seeded manager - should set httpOnly cookie and return user data
    res = client.post('/auth/login', json={'email': 'manager@test.com', 'password': 'adminpass'})
    assert res.status_code == 200

    # Check that JWT cookie is set
    assert 'jwt' in res.headers.get('Set-Cookie', '')

    # Check response contains user data but no token
    data = res.get_json()
    assert 'user' in data
    assert 'token' not in data  # No token in response body
    assert data['user']['email'] == 'manager@test.com'
    assert data['user']['role'] == 'Manager'

    # Login seeded employee - should set httpOnly cookie and return user data
    res = client.post('/auth/login', json={'email': 'employee1@company.com', 'password': 'employeepass'})
    assert res.status_code == 200

    # Check that JWT cookie is set
    assert 'jwt' in res.headers.get('Set-Cookie', '')

    # Check response contains user data but no token
    data = res.get_json()
    assert 'user' in data
    assert 'token' not in data  # No token in response body
    assert data['user']['email'] == 'employee1@company.com'
    assert data['user']['role'] == 'Employee'

def test_register_new_user(client):
    email = 'newuser@test.com'
    password = 'password123'

    # Register
    res = client.post('/auth/register', json={'name': 'New User', 'email': email, 'password': password})
    assert res.status_code == 201

    # User should exist in DB (modern SQLAlchemy 2.x style)
    user = db.session.execute(
        db.select(User).filter_by(email=email)
    ).scalar_one_or_none()
    assert user is not None
    assert user.email == email
    assert user.name == 'New User'

    # Login should succeed (no verification required in this implementation)
    res = client.post('/auth/login', json={'email': email, 'password': password})
    assert res.status_code == 200

    # Check that JWT cookie is set
    assert 'jwt' in res.headers.get('Set-Cookie', '')

    # Check response contains user data
    data = res.get_json()
    assert 'user' in data
    assert data['user']['email'] == email
