import logging
from flask import Blueprint, request, jsonify, abort
from datetime import datetime
from app.models import db, Task, Project, User

task_bp = Blueprint('tasks', __name__, url_prefix='/tasks')

# -----------------------------
# Configure logger
# -----------------------------
logger = logging.getLogger(__name__)
logger.setLevel(logging.INFO)

# -----------------------------
# Get all tasks
# -----------------------------
@task_bp.route('/', methods=['GET'])
def get_tasks():
    tasks = db.session.query(Task).all()
    return jsonify([
        {
            'id': t.id,
            'title': t.title,
            'description': t.description,
            'status': t.status,
            'priority': t.priority,
            'due_date': t.due_date.isoformat() if t.due_date else None,
            'sprint_id': t.sprint_id,
            'project_id': t.project_id,
            'assignee_id': t.assignee_id,
            'created_at': t.created_at.isoformat()
        } for t in tasks
    ]), 200

# -----------------------------
# Get a single task by ID
# -----------------------------
@task_bp.route('/<int:task_id>', methods=['GET'])
def get_task(task_id):
    task = db.session.get(Task, task_id)
    if not task:
        abort(404, description="Task not found")
    return jsonify({
        'id': task.id,
        'title': task.title,
        'description': task.description,
        'status': task.status,
        'priority': task.priority,
        'due_date': task.due_date.isoformat() if task.due_date else None,
        'sprint_id': task.sprint_id,
        'project_id': task.project_id,
        'assignee_id': task.assignee_id,
        'created_at': task.created_at.isoformat()
    }), 200

# -----------------------------
# Create a new task
# -----------------------------
@task_bp.route('/', methods=['POST'])
def create_task():
    data = request.get_json() or {}
    required_fields = ['title', 'project_id']
    if not all(field in data for field in required_fields):
        return jsonify({'error': 'Missing required fields'}), 400

    project = db.session.get(Project, data['project_id'])
    if not project:
        return jsonify({'error': 'Project not found'}), 404

    assignee_id = data.get('assignee_id')
    if assignee_id:
        assignee = db.session.get(User, assignee_id)
        if not assignee:
            return jsonify({'error': 'Assignee not found'}), 404
        assignee_id = assignee.id

    due_date = None
    if data.get('due_date'):
        due_date = datetime.fromisoformat(data['due_date'].replace('Z', '+00:00'))

    new_task = Task(
        title=data['title'],
        description=data.get('description'),
        project_id=project.id,
        assignee_id=assignee_id,
        sprint_id=data.get('sprint_id'),
        status=data.get('status', 'To Do'),
        priority=data.get('priority', 'Medium'),
        due_date=due_date
    )

    db.session.add(new_task)
    db.session.commit()
    logger.info(f"Task {new_task.id} created for project {project.id}")
    return jsonify({'message': 'Task created successfully', 'task_id': new_task.id}), 201

# -----------------------------
# Update a task
# -----------------------------
@task_bp.route('/<int:task_id>', methods=['PUT'])
def update_task(task_id):
    task = db.session.get(Task, task_id)
    if not task:
        abort(404, description="Task not found")

    data = request.get_json() or {}

    if 'title' in data:
        task.title = data['title']
    if 'description' in data:
        task.description = data['description']
    if 'status' in data:
        task.status = data['status']
    if 'priority' in data:
        task.priority = data['priority']
    if 'sprint_id' in data:
        task.sprint_id = data['sprint_id']
    if 'due_date' in data:
        if data['due_date']:
            task.due_date = datetime.fromisoformat(data['due_date'].replace('Z', '+00:00'))
        else:
            task.due_date = None
    if 'assignee_id' in data:
        assignee = db.session.get(User, data['assignee_id'])
        if not assignee:
            return jsonify({'error': 'Assignee not found'}), 404
        task.assignee_id = assignee.id

    db.session.commit()
    logger.info(f"Task {task.id} updated")
    return jsonify({'message': 'Task updated successfully'}), 200

# -----------------------------
# Delete a task
# -----------------------------
@task_bp.route('/<int:task_id>', methods=['DELETE'])
def delete_task(task_id):
    task = db.session.get(Task, task_id)
    if not task:
        abort(404, description="Task not found")
    db.session.delete(task)
    db.session.commit()
    logger.info(f"Task {task.id} deleted")
    return jsonify({'message': 'Task deleted successfully'}), 200

# -----------------------------
# Get all tasks for a specific project
# -----------------------------
@task_bp.route('/project/<int:project_id>', methods=['GET'])
def get_tasks_by_project(project_id):
    tasks = db.session.query(Task).filter_by(project_id=project_id).all()
    return jsonify({
        'tasks': [
            {
                'id': t.id,
                'title': t.title,
                'description': t.description,
                'status': t.status,
                'priority': t.priority,
                'due_date': t.due_date.isoformat() if t.due_date else None,
                'sprint_id': t.sprint_id,
                'assignee_id': t.assignee_id,
                'assignee': {
                    'id': t.assignee.id,
                    'name': t.assignee.name,
                    'email': t.assignee.email
                } if t.assignee else None
            } for t in tasks
        ]
    }), 200
