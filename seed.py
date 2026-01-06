import os
from datetime import datetime, date
from app.models import db, User, Cohort, Project, ProjectMember, ActivityLog, Task, Class
from run import create_app
from sqlalchemy import text

# -----------------------------
# Load environment variables for passwords
# -----------------------------
MANAGER_PASSWORD = os.environ.get("MANAGER_PASSWORD", "adminpass")
EMPLOYEE_PASSWORD = os.environ.get("EMPLOYEE_PASSWORD", "employeepass")

# -----------------------------
# Initialize app context
# -----------------------------
app = create_app()

with app.app_context():
    # -----------------------------
    # Truncate tables & reset identities
    # -----------------------------
    print("⚠️ Truncating all tables...")
    db.session.execute(
        text('TRUNCATE TABLE users, cohorts, classes, projects, project_members, tasks, activity_logs RESTART IDENTITY CASCADE')
    )
    db.session.commit()

    # -----------------------------
    # Seed Classes
    # -----------------------------
    print("⚡ Seeding project types...")
    project_types = [
        Class(name="Web Application"),
        Class(name="Mobile Development"),
        Class(name="Data Analytics"),
        Class(name="DevOps & Infrastructure"),
        Class(name="Product Management"),
        Class(name="Cybersecurity"),
    ]
    db.session.add_all(project_types)
    db.session.commit()
    print(f"✅ Project types seeded: {len(project_types)} types")

    # -----------------------------
    # Seed Users
    # -----------------------------
    print("⚡ Seeding users...")
    manager = User(
        name="Manager User",
        email="manager@test.com",
        role="Manager"
    )
    manager.set_password(MANAGER_PASSWORD)

    employees = []
    for i in range(1, 6):
        employee = User(
            name=f"Employee {i}",
            email=f"employee{i}@company.com",
            role="Employee"
        )
        employee.set_password(EMPLOYEE_PASSWORD)

        # Assign a project type deterministically
        employee.class_id = project_types[i % len(project_types)].id

        employees.append(employee)

    db.session.add(manager)
    db.session.add_all(employees)
    db.session.commit()
    print("✅ Users seeded: 1 Manager + 5 Employees")

    # -----------------------------
    # Seed additional test users for pytest
    # -----------------------------
    test_users = [
        {"name": "Owner Test", "email": "owner@test.com", "role": "Employee", "password": "pass", "project_type": project_types[0]},
        {"name": "User1 Test", "email": "user1@test.com", "role": "Employee", "password": "employeepass", "project_type": project_types[1]},
        {"name": "Employee Test", "email": "employee@test.com", "role": "Employee", "password": "employeepass", "project_type": project_types[2]},
    ]

    for u in test_users:
        user = User(name=u["name"], email=u["email"], role=u["role"])
        user.set_password(u["password"])
        user.class_id = u["project_type"].id
        db.session.add(user)
    db.session.commit()
    print("✅ Test users seeded for pytest")

    # -----------------------------
    # Seed Cohorts
    # -----------------------------
    print("⚡ Seeding teams...")
    teams = [
        Cohort(
            name="Frontend Team",
            start_date=date(2025, 1, 15),
            end_date=date(2025, 6, 30)
        ),
        Cohort(
            name="Backend Team",
            start_date=date(2025, 7, 1),
            end_date=date(2025, 12, 15)
        )
    ]
    db.session.add_all(teams)
    db.session.commit()
    print("✅ Teams seeded: 2 teams")

    # Assign employees to teams deterministically
    for i, employee in enumerate(employees):
        employee.cohort_id = teams[i % len(teams)].id
    db.session.commit()
    print("✅ Employees assigned to teams")

    # -----------------------------
    # Seed Projects
    # -----------------------------
    print("⚡ Seeding projects...")
    project_templates = [
        {"name": "Project X", "description": "Fullstack web app", "track": "Fullstack"},
        {"name": "Project Y", "description": "Data analysis project", "track": "Data Science"},
        {"name": "Project Z", "description": "Mobile app", "track": "Mobile"},
    ]

    tags_by_track = {
        "Fullstack": ["Python", "Flask", "React", "PostgreSQL"],
        "Data Science": ["Python", "Pandas", "NumPy", "Machine Learning"],
        "Mobile": ["Android", "Java", "Kotlin", "Flutter"]
    }

    statuses = ["In Progress", "Completed", "Under Review"]
    projects = []

    for i, template in enumerate(project_templates):
        owner = employees[i % len(employees)]
        project = Project(
            name=template["name"],
            description=template["description"],
            owner_id=owner.id,
            class_id=owner.class_id,  # Assign same project type as the owner
            cohort_id=owner.cohort_id,  # Assign same team as the owner
            github_link=f"https://github.com/{owner.email.split('@')[0]}/{template['name'].replace(' ', '').lower()}",
            status=statuses[i % len(statuses)]
        )
        projects.append(project)

    db.session.add_all(projects)
    db.session.commit()
    print(f"✅ Projects seeded: {len(projects)} projects")

    # -----------------------------
    # Seed Project Members + Activity Logs
    # -----------------------------
    print("⚡ Seeding project members & activity logs...")
    for project in projects:
        possible_members = [e for e in employees if e.id != project.owner_id]
        members_to_add = possible_members[:2]
        for member in members_to_add:
            db.session.add(ProjectMember(project_id=project.id, user_id=member.id, status="accepted"))
            db.session.add(ActivityLog(user_id=member.id, action=f"Joined project {project.name}"))

        db.session.add(ActivityLog(user_id=project.owner_id, action=f"Created project {project.name}"))

        if project.status == "Completed":
            db.session.add(ActivityLog(user_id=project.owner_id, action=f"Marked project {project.name} as Completed"))

    db.session.commit()
    print("✅ Project members & activity logs seeded")

    # -----------------------------
    # Seed Tasks for each Project
    # -----------------------------
    print("⚡ Seeding tasks...")
    task_templates = [
        "Setup project repository",
        "Design database schema",
        "Implement authentication",
        "Build REST API endpoints",
        "Connect frontend with backend",
        "Write unit tests",
        "Prepare documentation"
    ]

    task_statuses = ["To Do", "In Progress", "Completed"]

    for project in projects:
        for i in range(3):
            task = Task(
                title=task_templates[i],
                description=f"Task {i+1} for {project.name}",
                status=task_statuses[i % len(task_statuses)],
                project_id=project.id,
                assignee_id=employees[i % len(employees)].id,
                created_at=datetime.utcnow()
            )
            db.session.add(task)

        db.session.add(ActivityLog(user_id=project.owner_id, action=f"Created 3 tasks for {project.name}"))

    db.session.commit()
    print("✅ Tasks seeded for each project")

    # -----------------------------
    # Seed Admin Activity Logs
    # -----------------------------
    manager_logs = [
        ActivityLog(user_id=manager.id, action="Seeded database with manager, employees, and tasks"),
        ActivityLog(user_id=manager.id, action="Reviewed all project submissions")
    ]
    db.session.add_all(manager_logs)
    db.session.commit()

    print("🎉 Database seeded successfully! 2FA is disabled by default. Users can enable it after login.")
