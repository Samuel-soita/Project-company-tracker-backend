from flask import Blueprint, request, jsonify
from functools import wraps
from app.models import db, TimeLog, Task
from datetime import datetime, timezone
import jwt
import os

time_routes = Blueprint('time_routes', __name__)

def token_required(f):
    @wraps(f)
    def decorated(*args, **kwargs):
        token = request.cookies.get('token')
        if not token:
            return jsonify({'message': 'Token is missing!'}), 401
        try:
            data = jwt.decode(token, os.getenv('SECRET_KEY', 'super-secret-key'), algorithms=['HS256'])
            current_user = data
        except:
            return jsonify({'message': 'Token is invalid!'}), 401
        return f(current_user, *args, **kwargs)
    return decorated

@time_routes.route('/tasks/<int:task_id>/time', methods=['GET'])
@token_required
def get_time_logs(current_user, task_id):
    logs = TimeLog.query.filter_by(task_id=task_id).order_by(TimeLog.created_at.desc()).all()
    total_hours = sum([log.hours_spent for log in logs])
    
    log_list = []
    for log in logs:
        log_list.append({
            'id': log.id,
            'user_id': log.user_id,
            'user_name': log.user.name if log.user else 'Unknown',
            'hours_spent': log.hours_spent,
            'date_logged': log.date_logged.isoformat() if log.date_logged else None,
            'description': log.description
        })
    
    return jsonify({
        'total_hours': total_hours,
        'logs': log_list
    }), 200

@time_routes.route('/tasks/<int:task_id>/time', methods=['POST'])
@token_required
def log_time(current_user, task_id):
    data = request.get_json()
    
    if not data or 'hours_spent' not in data:
        return jsonify({'message': 'hours_spent is required'}), 400

    new_log = TimeLog(
        task_id=task_id,
        user_id=current_user['id'],
        hours_spent=float(data['hours_spent']),
        date_logged=datetime.strptime(data.get('date_logged', datetime.now().strftime('%Y-%m-%d')), '%Y-%m-%d').date(),
        description=data.get('description', '')
    )
    
    db.session.add(new_log)
    db.session.commit()
    
    return jsonify({'message': 'Time logged successfully', 'log': {'id': new_log.id, 'hours_spent': new_log.hours_spent}}), 201

@time_routes.route('/time/<int:log_id>', methods=['DELETE'])
@token_required
def delete_time_log(current_user, log_id):
    log = TimeLog.query.get_or_404(log_id)
    if log.user_id != current_user['id'] and current_user.get('role') != 'Manager':
        return jsonify({'message': 'Unauthorized to delete this time log'}), 403
        
    db.session.delete(log)
    db.session.commit()
    return jsonify({'message': 'Time log deleted successfully'})
