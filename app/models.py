from flask_sqlalchemy import SQLAlchemy
from werkzeug.security import generate_password_hash, check_password_hash
from datetime import datetime, timezone

db = SQLAlchemy()

# -----------------------------
# Association table for Project Members
# -----------------------------
class ProjectMember(db.Model):
    __tablename__ = 'project_members'
    id = db.Column(db.Integer, primary_key=True)
    project_id = db.Column(db.Integer, db.ForeignKey('projects.id', ondelete='CASCADE'))
    user_id = db.Column(db.Integer, db.ForeignKey('users.id', ondelete='CASCADE'))
    status = db.Column(db.String(20), default='pending')  # pending, accepted
    role = db.Column(db.String(50), default='collaborator')  # collaborator, viewer, owner
    created_at = db.Column(db.DateTime(timezone=True), default=lambda: datetime.now(timezone.utc))
    joined_at = db.Column(db.DateTime(timezone=True), nullable=True)

    user = db.relationship('User', back_populates='project_memberships', foreign_keys=[user_id])
    project = db.relationship('Project', back_populates='members')

# -----------------------------
# Activity Logs
# -----------------------------
class ActivityLog(db.Model):
    __tablename__ = 'activity_logs'
    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer, db.ForeignKey('users.id'))
    action = db.Column(db.String(255), nullable=False)
    created_at = db.Column(db.DateTime(timezone=True), default=lambda: datetime.now(timezone.utc))

# -----------------------------
# Classes / Specializations
# -----------------------------
class Class(db.Model):
    __tablename__ = 'classes'
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(150), unique=True, nullable=False)  # e.g., Fullstack Android
    created_at = db.Column(db.DateTime(timezone=True), default=lambda: datetime.now(timezone.utc))

    students = db.relationship('User', back_populates='class_model', lazy=True)

# -----------------------------
# Users
# -----------------------------
class User(db.Model):
    __tablename__ = 'users'
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(150), nullable=False)
    email = db.Column(db.String(150), unique=True, nullable=False)
    password_hash = db.Column(db.String(512), nullable=False)
    role = db.Column(db.String(50), default='Employee')
    created_at = db.Column(db.DateTime(timezone=True), default=lambda: datetime.now(timezone.utc))

    cohort_id = db.Column(db.Integer, db.ForeignKey('cohorts.id'), nullable=True)
    cohort = db.relationship('Cohort', backref='students')

    class_id = db.Column(db.Integer, db.ForeignKey('classes.id'), nullable=True)

    two_factor_enabled = db.Column(db.Boolean, default=False)
    two_factor_secret = db.Column(db.String(255), nullable=True)

    owned_projects = db.relationship('Project', backref='owner', lazy=True)
    project_memberships = db.relationship('ProjectMember', back_populates='user', cascade="all, delete-orphan")
    activities = db.relationship('ActivityLog', backref='user', lazy=True)
    tasks = db.relationship('Task', back_populates='assignee', lazy=True, cascade="all, delete-orphan")
    class_model = db.relationship('Class', back_populates='students')
    time_logs = db.relationship('TimeLog', back_populates='user', lazy=True)
    notifications = db.relationship('Notification', back_populates='user', lazy=True, cascade="all, delete-orphan")

    def set_password(self, password):
        self.password_hash = generate_password_hash(password)

    def check_password(self, password):
        return check_password_hash(self.password_hash, password)

# -----------------------------
# Projects
# -----------------------------
class Project(db.Model):
    __tablename__ = 'projects'
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(150), nullable=False)
    description = db.Column(db.Text, nullable=True)
    owner_id = db.Column(db.Integer, db.ForeignKey('users.id', ondelete='SET NULL'))
    class_id = db.Column(db.Integer, db.ForeignKey('classes.id', ondelete='SET NULL'), nullable=True)
    cohort_id = db.Column(db.Integer, db.ForeignKey('cohorts.id', ondelete='SET NULL'), nullable=True)
    github_link = db.Column(db.String(255), nullable=True)
    status = db.Column(db.String(50), default='In Progress')
    created_at = db.Column(db.DateTime(timezone=True), default=lambda: datetime.now(timezone.utc))
    updated_at = db.Column(db.DateTime(timezone=True), default=lambda: datetime.now(timezone.utc), onupdate=lambda: datetime.now(timezone.utc))

    members = db.relationship('ProjectMember', back_populates='project', lazy=True, cascade="all, delete-orphan")
    tasks = db.relationship('Task', back_populates='project', lazy=True, cascade="all, delete-orphan")
    comments = db.relationship('Comment', back_populates='project', lazy=True, cascade="all, delete-orphan")
    attachments = db.relationship('Attachment', back_populates='project', lazy=True, cascade="all, delete-orphan")
    sprints = db.relationship('Sprint', back_populates='project', lazy=True, cascade="all, delete-orphan")
    class_ref = db.relationship('Class', backref='projects', lazy=True)
    cohort = db.relationship('Cohort', backref='projects', lazy=True)

# -----------------------------
# Tasks
# -----------------------------
class Task(db.Model):
    __tablename__ = 'tasks'
    id = db.Column(db.Integer, primary_key=True)
    title = db.Column(db.String(150), nullable=False)
    description = db.Column(db.Text, nullable=True)
    project_id = db.Column(db.Integer, db.ForeignKey('projects.id', ondelete='CASCADE'))
    assignee_id = db.Column(db.Integer, db.ForeignKey('users.id', ondelete='SET NULL'), nullable=True)
    sprint_id = db.Column(db.Integer, db.ForeignKey('sprints.id', ondelete='SET NULL'), nullable=True)
    status = db.Column(db.String(50), default='To Do')
    priority = db.Column(db.String(50), default='Medium') # Low, Medium, High, Urgent
    due_date = db.Column(db.DateTime(timezone=True), nullable=True)
    created_at = db.Column(db.DateTime(timezone=True), default=lambda: datetime.now(timezone.utc))

    project = db.relationship('Project', back_populates='tasks')
    assignee = db.relationship('User', back_populates='tasks')
    sprint = db.relationship('Sprint', back_populates='tasks')
    comments = db.relationship('Comment', back_populates='task', lazy=True, cascade="all, delete-orphan")
    attachments = db.relationship('Attachment', back_populates='task', lazy=True, cascade="all, delete-orphan")
    time_logs = db.relationship('TimeLog', back_populates='task', lazy=True, cascade="all, delete-orphan")

# -----------------------------
# Sprints
# -----------------------------
class Sprint(db.Model):
    __tablename__ = 'sprints'
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(150), nullable=False)
    project_id = db.Column(db.Integer, db.ForeignKey('projects.id', ondelete='CASCADE'))
    start_date = db.Column(db.DateTime(timezone=True), nullable=True)
    end_date = db.Column(db.DateTime(timezone=True), nullable=True)
    status = db.Column(db.String(50), default='Planning') # Planning, Active, Completed
    created_at = db.Column(db.DateTime(timezone=True), default=lambda: datetime.now(timezone.utc))

    project = db.relationship('Project', back_populates='sprints')
    tasks = db.relationship('Task', back_populates='sprint', lazy=True)

# -----------------------------
# Time Logs
# -----------------------------
class TimeLog(db.Model):
    __tablename__ = 'time_logs'
    id = db.Column(db.Integer, primary_key=True)
    task_id = db.Column(db.Integer, db.ForeignKey('tasks.id', ondelete='CASCADE'))
    user_id = db.Column(db.Integer, db.ForeignKey('users.id', ondelete='CASCADE'))
    hours_spent = db.Column(db.Float, nullable=False)
    date_logged = db.Column(db.Date, nullable=False)
    description = db.Column(db.Text, nullable=True)
    created_at = db.Column(db.DateTime(timezone=True), default=lambda: datetime.now(timezone.utc))

    task = db.relationship('Task', back_populates='time_logs')
    user = db.relationship('User', back_populates='time_logs')

# -----------------------------
# Comments
# -----------------------------
class Comment(db.Model):
    __tablename__ = 'comments'
    id = db.Column(db.Integer, primary_key=True)
    content = db.Column(db.Text, nullable=False)
    author_id = db.Column(db.Integer, db.ForeignKey('users.id', ondelete='SET NULL'))
    project_id = db.Column(db.Integer, db.ForeignKey('projects.id', ondelete='CASCADE'), nullable=True)
    task_id = db.Column(db.Integer, db.ForeignKey('tasks.id', ondelete='CASCADE'), nullable=True)
    created_at = db.Column(db.DateTime(timezone=True), default=lambda: datetime.now(timezone.utc))

    author = db.relationship('User', backref='comments')
    project = db.relationship('Project', back_populates='comments')
    task = db.relationship('Task', back_populates='comments')

# -----------------------------
# Attachments
# -----------------------------
class Attachment(db.Model):
    __tablename__ = 'attachments'
    id = db.Column(db.Integer, primary_key=True)
    file_name = db.Column(db.String(255), nullable=False)
    file_url = db.Column(db.String(512), nullable=False)
    file_type = db.Column(db.String(50), nullable=True)
    uploader_id = db.Column(db.Integer, db.ForeignKey('users.id', ondelete='SET NULL'))
    project_id = db.Column(db.Integer, db.ForeignKey('projects.id', ondelete='CASCADE'), nullable=True)
    task_id = db.Column(db.Integer, db.ForeignKey('tasks.id', ondelete='CASCADE'), nullable=True)
    created_at = db.Column(db.DateTime(timezone=True), default=lambda: datetime.now(timezone.utc))

    uploader = db.relationship('User', backref='attachments')
    project = db.relationship('Project', back_populates='attachments')
    task = db.relationship('Task', back_populates='attachments')

# -----------------------------
# Cohorts
# -----------------------------
class Cohort(db.Model):
    __tablename__ = 'cohorts'
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(150), nullable=False)
    start_date = db.Column(db.Date, nullable=True)
    end_date = db.Column(db.Date, nullable=True)
    created_at = db.Column(db.DateTime(timezone=True), default=lambda: datetime.now(timezone.utc))

# -----------------------------
# Notifications
# -----------------------------
class Notification(db.Model):
    __tablename__ = 'notifications'
    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer, db.ForeignKey('users.id', ondelete='CASCADE'))
    type = db.Column(db.String(50), nullable=False)
    message = db.Column(db.Text, nullable=False)
    is_read = db.Column(db.Boolean, default=False)
    link = db.Column(db.String(255), nullable=True)
    created_at = db.Column(db.DateTime(timezone=True), default=lambda: datetime.now(timezone.utc))

    user = db.relationship('User', back_populates='notifications')
