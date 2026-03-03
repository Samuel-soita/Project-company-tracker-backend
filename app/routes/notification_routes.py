from flask import Blueprint, jsonify
from app.models import db, Notification
from app.utils.auth import token_required

notification_routes = Blueprint('notification_routes', __name__)

@notification_routes.route('/notifications', methods=['GET'])
@token_required
def get_notifications(current_user):
    notifications = Notification.query.filter_by(user_id=current_user.id).order_by(Notification.created_at.desc()).limit(20).all()
    return jsonify({
        'notifications': [{
            'id': n.id,
            'type': n.type,
            'message': n.message,
            'is_read': n.is_read,
            'link': n.link,
            'created_at': n.created_at.isoformat() if n.created_at else None
        } for n in notifications]
    }), 200

@notification_routes.route('/notifications/<int:notification_id>/read', methods=['PATCH'])
@token_required
def mark_read(current_user, notification_id):
    notification = db.session.get(Notification, notification_id)
    if not notification:
        return jsonify({'message': 'Notification not found'}), 404
        
    if notification.user_id != current_user.id:
        return jsonify({'message': 'Not authorized'}), 403
        
    notification.is_read = True
    db.session.commit()
    
    return jsonify({'message': 'Marked as read'}), 200
