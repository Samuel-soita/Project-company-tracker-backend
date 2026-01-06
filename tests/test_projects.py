import pytest
from app.models import User, Project, Cohort, db

# -----------------------------
# Helper: Login as user (sets cookie automatically)
# -----------------------------
def login_as_user_with_cohort(client, email, password, cohort_id=None):
    user = db.session.execute(
        db.select(User).filter_by(email=email)
    ).scalar_one_or_none()

    if not user:
        # If user not seeded, create
        user = User(name=email.split('@')[0], email=email, role='Student')
        user.set_password(password)
        if cohort_id:
            user.cohort_id = cohort_id
        db.session.add(user)
        db.session.commit()

    login = client.post('/auth/login', json={'email': email, 'password': password})
    assert login.status_code == 200
    # Cookie is automatically set for subsequent requests

# -----------------------------
# Test Project CRUD
# -----------------------------
def test_project_crud(client):
    # -----------------------------
    # Prepare cohort and class for student
    # -----------------------------
    from app.models import Class
    cohort = db.session.execute(
        db.select(Cohort).filter_by(name='Fullstack 101')
    ).scalar_one_or_none()

    if not cohort:
        cohort = Cohort(name='Fullstack 101')
        db.session.add(cohort)
        db.session.commit()

    class_obj = db.session.execute(
        db.select(Class).filter_by(name='Fullstack Web')
    ).scalar_one_or_none()

    if not class_obj:
        class_obj = Class(name='Fullstack Web')
        db.session.add(class_obj)
        db.session.commit()

    # -----------------------------
    # Student with cohort and class - login sets cookie automatically
    # -----------------------------
    user = db.session.execute(
        db.select(User).filter_by(email='user1@test.com')
    ).scalar_one_or_none()

    if not user:
        user = User(name='User1', email='user1@test.com', role='Student')
        user.set_password('pass')
        user.cohort_id = cohort.id
        user.class_id = class_obj.id
        db.session.add(user)
        db.session.commit()

    login = client.post('/auth/login', json={'email': 'user1@test.com', 'password': 'pass'})
    assert login.status_code == 200

    project_data = {
        'name': 'Project X',
        'description': 'Test project',
        'class_id': class_obj.id,
        'cohort_id': cohort.id,
        'tags': ['Fullstack']
    }

    # Create project (should succeed)
    res = client.post('/projects', json=project_data, )
    assert res.status_code == 201
    project_id = res.json['id']

    # -----------------------------
    # Student without cohort - should fail to create project
    # -----------------------------
    user2 = db.session.execute(
        db.select(User).filter_by(email='user2@test.com')
    ).scalar_one_or_none()

    if not user2:
        user2 = User(name='User2', email='user2@test.com', role='Student')
        user2.set_password('pass')
        # Note: no cohort_id assigned
        db.session.add(user2)
        db.session.commit()

    login2 = client.post('/auth/login', json={'email': 'user2@test.com', 'password': 'pass'})
    assert login2.status_code == 200

    res = client.post('/projects', json=project_data)
    assert res.status_code == 403
    assert 'cohort' in res.json['message'].lower()

    # -----------------------------
    # Retrieve project
    # -----------------------------
    res = client.get(f'/projects/{project_id}')
    assert res.status_code == 200
    assert res.json['project']['name'] == project_data['name']

    # -----------------------------
    # Re-login as the original user (user1) to update project
    # -----------------------------
    login = client.post('/auth/login', json={'email': 'user1@test.com', 'password': 'pass'})
    assert login.status_code == 200

    updated_data = {'name': 'Project X Updated', 'tags': ['Fullstack', 'Python']}
    res = client.put(f'/projects/{project_id}', json=updated_data)
    assert res.status_code == 200
    res = client.get(f'/projects/{project_id}')
    assert res.json['project']['name'] == 'Project X Updated'

    # -----------------------------
    # Change project status
    # -----------------------------
    res = client.patch(f'/projects/{project_id}/status', json={'status': 'Under Review'}, )
    assert res.status_code == 200
    res = client.get(f'/projects/{project_id}')
    assert res.json['project']['status'] == 'Under Review'

    # -----------------------------
    # Delete project
    # -----------------------------
    res = client.delete(f'/projects/{project_id}', )
    assert res.status_code == 200

    # Verify deletion
    res = client.get(f'/projects/{project_id}', )
    assert res.status_code == 404