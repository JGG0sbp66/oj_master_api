from flask import Blueprint, request, jsonify, current_app
from ..services.auth_service import register_user, login_user, logout_user
from ..utils.validators import validate_credentials
import jwt

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


@auth_bp.route('/verify-token', methods=['GET'])
def verify_token():
    token = request.cookies.get('auth_token')
    if not token:
        return jsonify({'authenticated': False}), 401

    try:
        data = jwt.decode(token, current_app.config['SECRET_KEY'], algorithms=["HS256"])
        return jsonify({
            'authenticated': True,
            'user': {
                'uid': data['uid'],
                'username': data['username'],
                'role': data['role']
            }
        })
    except jwt.ExpiredSignatureError:
        return jsonify({'authenticated': False, 'message': 'Token已过期'}), 401
    except jwt.InvalidTokenError:
        return jsonify({'authenticated': False, 'message': '无效Token'}), 401


@auth_bp.route('/logout', methods=['POST'])
def logout():
    """退出登录接口"""
    return logout_user()
