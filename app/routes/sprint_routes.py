from flask import Blueprint, request, jsonify
from app.models import db, Sprint, Project, ProjectMember, Task
from app.utils.auth import token_required

sprint_routes = Blueprint('sprint_routes', __name__)

@sprint_routes.route('/projects/<int:project_id>/sprints', methods=['GET'])
@token_required
def get_sprints(current_user, project_id):
    sprints = Sprint.query.filter_by(project_id=project_id).all()
    sprint_list = []
    for s in sprints:
        # Also return basic tasks info for sprint planner
        tasks = [{'id': t.id, 'title': t.title, 'status': t.status, 'priority': t.priority} for t in s.tasks]
        sprint_list.append({
            'id': s.id,
            'name': s.name,
            'start_date': s.start_date.isoformat() if s.start_date else None,
            'end_date': s.end_date.isoformat() if s.end_date else None,
            'status': s.status,
            'tasks': tasks
        })
    return jsonify({'sprints': sprint_list}), 200

@sprint_routes.route('/projects/<int:project_id>/sprints', methods=['POST'])
@token_required
def create_sprint(current_user, project_id):
    data = request.get_json()
    if not data or not data.get('name'):
        return jsonify({'message': 'Sprint name is required'}), 400
    
    # Optional authorization check could go here...

    new_sprint = Sprint(
        name=data['name'],
        project_id=project_id,
        status=data.get('status', 'Planning')
    )
    db.session.add(new_sprint)
    db.session.commit()
    
    return jsonify({
        'message': 'Sprint created successfully',
        'sprint': {
            'id': new_sprint.id,
            'name': new_sprint.name,
            'status': new_sprint.status
        }
    }), 201

@sprint_routes.route('/sprints/<int:sprint_id>', methods=['PUT'])
@token_required
def update_sprint(current_user, sprint_id):
    sprint = Sprint.query.get_or_404(sprint_id)
    data = request.get_json()

    if 'name' in data:
        sprint.name = data['name']
    if 'status' in data:
        sprint.status = data['status']
    
    db.session.commit()
    return jsonify({'message': 'Sprint updated successfully'})

@sprint_routes.route('/sprints/<int:sprint_id>', methods=['DELETE'])
@token_required
def delete_sprint(current_user, sprint_id):
    sprint = Sprint.query.get_or_404(sprint_id)
    # Removing a sprint should just delete the sprint, tasks will have their sprint_id set to NULL due to ondelete='SET NULL'
    db.session.delete(sprint)
    db.session.commit()
    return jsonify({'message': 'Sprint deleted successfully'})
