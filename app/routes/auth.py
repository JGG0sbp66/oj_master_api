from flask import Blueprint, request, jsonify, session
from ..services.auth_service import register_user, login_user
from ..utils.validators import validate_credentials

auth_bp = Blueprint('auth', __name__)


@auth_bp.route('/register', methods=['POST'])
def register():
    data = request.get_json()
    if not data:
        return jsonify({"success": False, "message": "请求数据必须是 JSON 格式"}), 400

    username = data.get('username', '').strip()
    password = data.get('password', '').strip()
    cfToken = data.get('cfToken', '').strip()

    # 验证输入
    validation_result = validate_credentials(username, password)
    if not validation_result['valid']:
        return jsonify({
            'success': False,
            'message': validation_result['message']
        }), 400

    # 调用服务层处理注册逻辑
    return register_user(username, password, cfToken)


@auth_bp.route('/login', methods=['POST'])
def login():
    data = request.get_json()
    if not data:
        return jsonify({"success": False, "message": "请求数据必须是 JSON 格式"}), 400

    username = data.get('username', '').strip()
    password = data.get('password', '').strip()

    if not all([username, password]):
        return jsonify({
            'success': False,
            'message': '用户名和密码均为必填字段'
        }), 400

    # 调用服务层处理登录逻辑
    return login_user(username, password)
