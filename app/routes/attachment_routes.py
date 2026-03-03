import os
import logging
from flask import Blueprint, request, jsonify
from app.models import db, Attachment, Project, Task, User
from app.utils.auth import token_required
from sqlalchemy.exc import SQLAlchemyError
import cloudinary
import cloudinary.uploader
from werkzeug.utils import secure_filename

attachment_routes = Blueprint('attachment_routes', __name__)
logger = logging.getLogger(__name__)

# Configure Cloudinary if credentials exist
if os.environ.get('CLOUDINARY_CLOUD_NAME'):
    cloudinary.config(
        cloud_name=os.environ.get('CLOUDINARY_CLOUD_NAME'),
        api_key=os.environ.get('CLOUDINARY_API_KEY'),
        api_secret=os.environ.get('CLOUDINARY_API_SECRET')
    )

ALLOWED_EXTENSIONS = {'png', 'jpg', 'jpeg', 'gif', 'pdf', 'doc', 'docx', 'txt', 'csv', 'xlsx'}

def allowed_file(filename):
    return '.' in filename and \
           filename.rsplit('.', 1)[1].lower() in ALLOWED_EXTENSIONS

@attachment_routes.route('/projects/<int:project_id>/attachments', methods=['GET'])
@token_required
def get_project_attachments(current_user, project_id):
    project = db.session.get(Project, project_id)
    if not project:
        return jsonify({'message': 'Project not found'}), 404
        
    attachments = Attachment.query.filter_by(project_id=project_id).order_by(Attachment.created_at.desc()).all()
    return jsonify({
        'attachments': [
            {
                'id': a.id,
                'file_name': a.file_name,
                'file_url': a.file_url,
                'file_type': a.file_type,
                'uploader_id': a.uploader_id,
                'uploader_name': a.uploader.name if a.uploader else 'Unknown',
                'created_at': a.created_at.isoformat()
            } for a in attachments
        ]
    }), 200

@attachment_routes.route('/projects/<int:project_id>/attachments', methods=['POST'])
@token_required
def add_project_attachment(current_user, project_id):
    project = db.session.get(Project, project_id)
    if not project:
        return jsonify({'message': 'Project not found'}), 404
        
    if 'file' not in request.files:
        return jsonify({'message': 'No file part'}), 400
        
    file = request.files['file']
    if file.filename == '':
        return jsonify({'message': 'No selected file'}), 400
        
    if not allowed_file(file.filename):
        return jsonify({'message': 'File type not allowed'}), 400
        
    try:
        # Upload to Cloudinary
        upload_result = cloudinary.uploader.upload(
            file,
            resource_type="auto",
            folder=f"project_tracker/projects/{project_id}"
        )
        
        attachment = Attachment(
            file_name=secure_filename(file.filename),
            file_url=upload_result.get('secure_url'),
            file_type=file.content_type,
            uploader_id=current_user.id,
            project_id=project_id
        )
        
        db.session.add(attachment)
        db.session.commit()
        return jsonify({
            'message': 'File uploaded',
            'attachment': {
                'id': attachment.id,
                'file_name': attachment.file_name,
                'file_url': attachment.file_url
            }
        }), 201
        
    except Exception as e:
        db.session.rollback()
        logger.error(f"Failed to upload attachment for project {project_id}: {str(e)}")
        return jsonify({'message': 'Failed to upload file. Check Cloudinary configuration.'}), 500

@attachment_routes.route('/tasks/<int:task_id>/attachments', methods=['GET'])
@token_required
def get_task_attachments(current_user, task_id):
    task = db.session.get(Task, task_id)
    if not task:
        return jsonify({'message': 'Task not found'}), 404
        
    attachments = Attachment.query.filter_by(task_id=task_id).order_by(Attachment.created_at.desc()).all()
    return jsonify({
        'attachments': [
            {
                'id': a.id,
                'file_name': a.file_name,
                'file_url': a.file_url,
                'file_type': a.file_type,
                'uploader_id': a.uploader_id,
                'uploader_name': a.uploader.name if a.uploader else 'Unknown',
                'created_at': a.created_at.isoformat()
            } for a in attachments
        ]
    }), 200

@attachment_routes.route('/tasks/<int:task_id>/attachments', methods=['POST'])
@token_required
def add_task_attachment(current_user, task_id):
    task = db.session.get(Task, task_id)
    if not task:
        return jsonify({'message': 'Task not found'}), 404
        
    if 'file' not in request.files:
        return jsonify({'message': 'No file part'}), 400
        
    file = request.files['file']
    if file.filename == '':
        return jsonify({'message': 'No selected file'}), 400
        
    if not allowed_file(file.filename):
        return jsonify({'message': 'File type not allowed'}), 400
        
    try:
        # Upload to Cloudinary
        upload_result = cloudinary.uploader.upload(
            file,
            resource_type="auto",
            folder=f"project_tracker/tasks/{task_id}"
        )
        
        attachment = Attachment(
            file_name=secure_filename(file.filename),
            file_url=upload_result.get('secure_url'),
            file_type=file.content_type,
            uploader_id=current_user.id,
            task_id=task_id
        )
        
        db.session.add(attachment)
        db.session.commit()
        return jsonify({
            'message': 'File uploaded',
            'attachment': {
                'id': attachment.id,
                'file_name': attachment.file_name,
                'file_url': attachment.file_url
            }
        }), 201
        
    except Exception as e:
        db.session.rollback()
        logger.error(f"Failed to upload attachment for task {task_id}: {str(e)}")
        return jsonify({'message': 'Failed to upload file. Check Cloudinary configuration.'}), 500

@attachment_routes.route('/attachments/<int:attachment_id>', methods=['DELETE'])
@token_required
def delete_attachment(current_user, attachment_id):
    attachment = db.session.get(Attachment, attachment_id)
    if not attachment:
        return jsonify({'message': 'Attachment not found'}), 404
        
    if current_user.role != 'Manager' and attachment.uploader_id != current_user.id:
        return jsonify({'message': 'Not authorized to delete this attachment'}), 403
        
    try:
        # We don't delete from cloudinary here to keep it simple, but we could by saving the public_id
        db.session.delete(attachment)
        db.session.commit()
        return jsonify({'message': 'Attachment deleted'}), 200
    except SQLAlchemyError as e:
        db.session.rollback()
        logger.error(f"Failed to delete attachment {attachment_id}: {str(e)}")
        return jsonify({'message': 'Failed to delete attachment'}), 500
