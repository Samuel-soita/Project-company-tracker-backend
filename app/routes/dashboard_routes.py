from flask import Blueprint, jsonify
from sqlalchemy import func
from app.models import db, Project, Task, Sprint
from app.utils.auth import token_required

dashboard_routes = Blueprint('dashboard_routes', __name__)

@dashboard_routes.route('/dashboard/manager-summary', methods=['GET'])
@token_required
def manager_summary(current_user):
    if current_user.role != 'Manager':
        return jsonify({'message': 'Not authorized'}), 403

    total_projects = Project.query.count()
    total_tasks = Task.query.count()
    active_sprints = Sprint.query.filter_by(status='Active').count()
    
    # Calculate some basic totals
    return jsonify({
        'totalProjects': total_projects,
        'totalTasks': total_tasks,
        'activeSprints': active_sprints
    }), 200

@dashboard_routes.route('/dashboard/projects-by-status', methods=['GET'])
@token_required
def projects_by_status(current_user):
    if current_user.role != 'Manager':
        return jsonify({'message': 'Not authorized'}), 403
        
    results = db.session.query(Project.status, func.count(Project.id)).group_by(Project.status).all()
    
    data = []
    for status, count in results:
        data.append({
            'name': status,
            'value': count
        })
        
    return jsonify({'data': data}), 200

@dashboard_routes.route('/dashboard/projects-by-team', methods=['GET'])
@token_required
def projects_by_team(current_user):
    if current_user.role != 'Manager':
        return jsonify({'message': 'Not authorized'}), 403
        
    from app.models import Cohort
    results = db.session.query(Cohort.name, func.count(Project.id)).join(Project, Cohort.id == Project.cohort_id).group_by(Cohort.name).all()
    
    data = []
    for team, count in results:
        data.append({
            'name': team,
            'value': count
        })
        
    return jsonify({'data': data}), 200

@dashboard_routes.route('/dashboard/task-productivity', methods=['GET'])
@token_required
def task_productivity(current_user):
    if current_user.role != 'Manager':
        return jsonify({'message': 'Not authorized'}), 403
        
    results = db.session.query(Task.status, func.count(Task.id)).group_by(Task.status).all()
    
    data = []
    for status, count in results:
        data.append({
            'name': status,
            'value': count
        })
        
    return jsonify({'data': data}), 200
