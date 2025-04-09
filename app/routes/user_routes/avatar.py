from flask import Blueprint, jsonify, request, send_from_directory

from app.services.avatar_service import get_avatar_service

avatar_bp = Blueprint('avatar', __name__)


@avatar_bp.route('/avatar-get/<int:user_id>', methods=['GET'])
def get_avatar(user_id):
    try:
        return get_avatar_service(user_id)
    except Exception as e:
        return jsonify({
            "success": False,
            "message": f"获取头像失败: {str(e)}"
        }), 500
