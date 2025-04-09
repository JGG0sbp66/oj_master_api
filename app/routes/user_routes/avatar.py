from flask import Blueprint, jsonify, g, request

from app.services.avatar_service import get_avatar_service, save_avatar
from app.utils.role_utils import optional_login

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


@avatar_bp.route('/avatar-upload', methods=['POST'])
@optional_login
def upload_avatar():
    try:
        user_id = getattr(g, 'current_user_id', None)
        if user_id is None:
            return jsonify({
                "success": False,
                "message": "无效的用户"
            }), 401

        print(request.files)

        # 检查是否有文件在请求中
        if 'file' not in request.files:
            return jsonify({
                "success": False,
                "message": "没有文件部分"
            }), 400

        file = request.files['file']

        # 调用函数保存头像
        filename = save_avatar(user_id, file)

        return jsonify({
            "success": True,
            "message": "头像更新成功",
            "filename": filename
        }), 200

    except Exception as e:
        return jsonify({
            "success": False,
            "message": f"更新头像失败: {str(e)}"
        }), 500
