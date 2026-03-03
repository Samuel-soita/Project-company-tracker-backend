import logging
from flask import Blueprint, request, jsonify
from app.models import db, Comment, Project, Task, User
from app.utils.auth import token_required
from sqlalchemy.exc import SQLAlchemyError

comment_routes = Blueprint('comment_routes', __name__)
logger = logging.getLogger(__name__)

@comment_routes.route('/projects/<int:project_id>/comments', methods=['GET'])
@token_required
def get_project_comments(current_user, project_id):
    project = db.session.get(Project, project_id)
    if not project:
        return jsonify({'message': 'Project not found'}), 404
        
    comments = Comment.query.filter_by(project_id=project_id).order_by(Comment.created_at.desc()).all()
    return jsonify({
        'comments': [
            {
                'id': c.id,
                'content': c.content,
                'author_id': c.author_id,
                'author_name': c.author.name if c.author else 'Unknown',
                'created_at': c.created_at.isoformat()
            } for c in comments
        ]
    }), 200

@comment_routes.route('/projects/<int:project_id>/comments', methods=['POST'])
@token_required
def add_project_comment(current_user, project_id):
    project = db.session.get(Project, project_id)
    if not project:
        return jsonify({'message': 'Project not found'}), 404
        
    data = request.get_json()
    if not data or not data.get('content'):
        return jsonify({'message': 'Comment content is required'}), 400
        
    comment = Comment(
        content=data['content'],
        author_id=current_user.id,
        project_id=project_id
    )
    
    try:
        db.session.add(comment)
        db.session.commit()
        return jsonify({'message': 'Comment added', 'comment_id': comment.id}), 201
    except SQLAlchemyError as e:
        db.session.rollback()
        logger.error(f"Failed to add comment to project {project_id}: {str(e)}")
        return jsonify({'message': 'Failed to add comment'}), 500

@comment_routes.route('/tasks/<int:task_id>/comments', methods=['GET'])
@token_required
def get_task_comments(current_user, task_id):
    task = db.session.get(Task, task_id)
    if not task:
        return jsonify({'message': 'Task not found'}), 404
        
    comments = Comment.query.filter_by(task_id=task_id).order_by(Comment.created_at.desc()).all()
    return jsonify({
        'comments': [
            {
                'id': c.id,
                'content': c.content,
                'author_id': c.author_id,
                'author_name': c.author.name if c.author else 'Unknown',
                'created_at': c.created_at.isoformat()
            } for c in comments
        ]
    }), 200

@comment_routes.route('/tasks/<int:task_id>/comments', methods=['POST'])
@token_required
def add_task_comment(current_user, task_id):
    task = db.session.get(Task, task_id)
    if not task:
        return jsonify({'message': 'Task not found'}), 404
        
    data = request.get_json()
    if not data or not data.get('content'):
        return jsonify({'message': 'Comment content is required'}), 400
        
    comment = Comment(
        content=data['content'],
        author_id=current_user.id,
        task_id=task_id
    )
    
    try:
        db.session.add(comment)
        db.session.commit()
        return jsonify({'message': 'Comment added', 'comment_id': comment.id}), 201
    except SQLAlchemyError as e:
        db.session.rollback()
        logger.error(f"Failed to add comment to task {task_id}: {str(e)}")
        return jsonify({'message': 'Failed to add comment'}), 500

@comment_routes.route('/comments/<int:comment_id>', methods=['DELETE'])
@token_required
def delete_comment(current_user, comment_id):
    comment = db.session.get(Comment, comment_id)
    if not comment:
        return jsonify({'message': 'Comment not found'}), 404
        
    if current_user.role != 'Manager' and comment.author_id != current_user.id:
        return jsonify({'message': 'Not authorized to delete this comment'}), 403
        
    try:
        db.session.delete(comment)
        db.session.commit()
        return jsonify({'message': 'Comment deleted'}), 200
    except SQLAlchemyError as e:
        db.session.rollback()
        logger.error(f"Failed to delete comment {comment_id}: {str(e)}")
        return jsonify({'message': 'Failed to delete comment'}), 500
