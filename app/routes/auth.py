from flask import Blueprint, request, jsonify, current_app
from ..services.auth_service import register_user, login_user, logout_user, repassword_user
from ..services.turnstile_service import check_cf_token, generate_code, send_verification_email, save_code_to_redis, \
    verify_email_code
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
    email = data.get('email', '').strip()
    email_code = data.get('email_code', '').strip()
    cfToken = data.get('cfToken', '').strip()

    # 验证输入
    validation_result = validate_credentials(username, password, email)
    if not validation_result['valid']:
        return jsonify({
            'success': False,
            'message': validation_result['message']
        }), 400

    # 调用服务层处理注册逻辑
    return register_user(username, password, email, email_code, cfToken)


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


@auth_bp.route('/repassword', methods=['POST'])
def repassword():
    data = request.get_json()
    if not data:
        return jsonify({"success": False, "message": "请求数据必须是 JSON 格式"}), 400

    username = data.get('username', '').strip()
    email = data.get('email', '').strip()
    email_code = data.get('email_code', '').strip()
    password = data.get('password', '').strip()

    if not all([username, email, email_code]):
        return jsonify({
            'success': False,
            'message': '请填写所有字段'
        }), 400

    return repassword_user(username, email, email_code, password)

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


@auth_bp.route('/verify-cf', methods=['POST'])
def verify():
    data = request.get_json()
    if not data:
        return jsonify({"success": False, "error": "请求数据必须是 JSON 格式"}), 400

    return check_cf_token(data)


# 发送验证码接口
@auth_bp.route('/send-email-code', methods=['POST'])
def send_verify_code():
    data = request.get_json()
    email = data.get("email")

    if not email:
        return jsonify({"success": False, "message": "邮箱不能为空"}), 400

    code = generate_code()
    if send_verification_email(email, code):
        save_code_to_redis(email, code)
        return jsonify({"success": True, "message": "验证码已发送"})
    else:
        return jsonify({"success": False, "message": "邮件发送失败"}), 500


# 校验验证码接口
@auth_bp.route('/verify-email-code', methods=['POST'])
def verify_code():
    data = request.get_json()
    email = data.get("email")
    user_code = data.get("code")

    if not all([email, user_code]):
        return jsonify({"success": False, "message": "参数不完整"}), 400

    return verify_email_code(email, user_code)
