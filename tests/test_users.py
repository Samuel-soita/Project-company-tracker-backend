import pytest
from app.models import User, db

# -----------------------------
# Helper: Login as user (sets cookie automatically)
# -----------------------------
def login_as_user(client, email, password):
    login = client.post('/auth/login', json={'email': email, 'password': password})
    assert login.status_code == 200
    # Cookie is automatically set for subsequent requests

# -----------------------------
# Test: User CRUD
# -----------------------------
def test_user_crud(client):
    # Use seeded manager - login sets cookie automatically
    manager_email = "manager@test.com"
    manager_password = "adminpass"
    login_as_user(client, manager_email, manager_password)

    # -----------------------------
    # Create new user
    # -----------------------------
    user_data = {'name': 'Test Student', 'email': 'student_test@test.com', 'password': 'pass', 'role': 'Student'}
    res = client.post('/users/', json=user_data)
    assert res.status_code == 201
    user_id = res.json['id']

    # -----------------------------
    # Auto-verify the new user so they can login
    # -----------------------------
    new_user = db.session.execute(
        db.select(User).filter_by(email=user_data['email'])
    ).scalar_one_or_none()
    assert new_user is not None
    new_user.is_verified = True
    db.session.commit()

    # -----------------------------
    # List users (admin only)
    # -----------------------------
    res = client.get('/users/', )
    assert res.status_code == 200
    assert any(u['id'] == user_id for u in res.json)

    # -----------------------------
    # Get user (admin access)
    # -----------------------------
    res = client.get(f'/users/{user_id}', )
    assert res.status_code == 200
    assert res.json['email'] == user_data['email']

    # -----------------------------
    # Update user (admin)
    # -----------------------------
    updated_data = {'name': 'Student Updated'}
    res = client.put(f'/users/{user_id}', json=updated_data, )
    assert res.status_code == 200

    # Verify update
    res = client.get(f'/users/{user_id}', )
    assert res.json['name'] == 'Student Updated'

    # -----------------------------
    # Self-update: student can update own name
    # -----------------------------
    # Login as the created student - cookie is set automatically
    login_as_user(client, user_data['email'], 'pass')
    res = client.put(f'/users/{user_id}', json={'name': 'Self Updated'})
    assert res.status_code == 200
    res = client.get(f'/users/{user_id}')
    assert res.json['name'] == 'Self Updated'

    # -----------------------------
    # Delete user (admin)
    # -----------------------------
    res = client.delete(f'/users/{user_id}', )
    assert res.status_code == 200

    # Verify deletion - should get 401 because user authentication fails (user no longer exists)
    res = client.get(f'/users/{user_id}')
    assert res.status_code == 401

# -----------------------------
# Test: Non-admin cannot list all users
# -----------------------------
def test_non_manager_list_users_denied(client):
    # Use seeded employee - login sets cookie automatically
    employee_email = "employee1@company.com"
    employee_password = "employeepass"
    login_as_user(client, employee_email, employee_password)

    res = client.get('/users/')
    assert res.status_code == 403
    assert 'not authorized' in res.json['message'].lower()
