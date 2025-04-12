from flask_restx import Resource, fields
from flask import request, current_app
from app import api
from app.services.auth_service import register_user, login_user, logout_user, repassword_user
from app.services.turnstile_service import check_cf_token, generate_code, send_verification_email, save_code_to_redis, \
    verify_email_code
from app.utils.validators import validate_credentials
import jwt

# 创建认证相关接口命名空间
auth_ns = api.namespace('Auth', description='用户认证相关接口', path='/api')

# 模型定义
register_model = auth_ns.model('Register', {
    'username': fields.String(required=True, description='用户名'),
    'password': fields.String(required=True, description='密码'),
    'email': fields.String(required=True, description='邮箱'),
    'email_code': fields.String(required=True, description='邮箱验证码'),
    'cfToken': fields.String(required=True, description='Cloudflare Turnstile验证令牌')
})

login_model = auth_ns.model('Login', {
    'username': fields.String(required=True, description='用户名'),
    'password': fields.String(required=True, description='密码')
})

repassword_model = auth_ns.model('Repassword', {
    'username': fields.String(required=True, description='用户名'),
    'email': fields.String(required=True, description='邮箱'),
    'email_code': fields.String(required=True, description='邮箱验证码'),
    'password': fields.String(required=True, description='新密码')
})

cf_verify_model = auth_ns.model('CFVerify', {
    'cfToken': fields.String(required=True, description='Cloudflare Turnstile验证令牌')
})

email_code_model = auth_ns.model('EmailCode', {
    'email': fields.String(required=True, description='邮箱地址')
})

verify_code_model = auth_ns.model('VerifyCode', {
    'email': fields.String(required=True, description='邮箱地址'),
    'code': fields.String(required=True, description='验证码')
})


@auth_ns.route('/register')
class Register(Resource):
    @auth_ns.doc(description='用户注册')
    @auth_ns.expect(register_model)
    def post(self):
        """用户注册接口"""
        data = request.get_json()
        if not data:
            return {"success": False, "message": "请求数据必须是 JSON 格式"}, 400

        username = data.get('username', '').strip()
        password = data.get('password', '').strip()
        email = data.get('email', '').strip()
        email_code = data.get('email_code', '').strip()
        cfToken = data.get('cfToken', '').strip()

        # 验证输入
        validation_result = validate_credentials(username, password, email)
        if not validation_result['valid']:
            return {
                'success': False,
                'message': validation_result['message']
            }, 400

        # 调用服务层处理注册逻辑
        return register_user(username, password, email, email_code, cfToken)


@auth_ns.route('/login')
class Login(Resource):
    @auth_ns.doc(description='用户登录')
    @auth_ns.expect(login_model)
    def post(self):
        """用户登录接口"""
        data = request.get_json()
        if not data:
            return {"success": False, "message": "请求数据必须是 JSON 格式"}, 400

        username = data.get('username', '').strip()
        password = data.get('password', '').strip()

        if not all([username, password]):
            return {
                'success': False,
                'message': '用户名和密码均为必填字段'
            }, 400

        # 调用服务层处理登录逻辑
        return login_user(username, password)


@auth_ns.route('/repassword')
class Repassword(Resource):
    @auth_ns.doc(description='重置密码')
    @auth_ns.expect(repassword_model)
    def post(self):
        """重置密码接口"""
        data = request.get_json()
        if not data:
            return {"success": False, "message": "请求数据必须是 JSON 格式"}, 400

        username = data.get('username', '').strip()
        email = data.get('email', '').strip()
        email_code = data.get('email_code', '').strip()
        password = data.get('password', '').strip()

        if not all([username, email, email_code]):
            return {
                'success': False,
                'message': '请填写所有字段'
            }, 400

        return repassword_user(username, email, email_code, password)


@auth_ns.route('/verify-token')
class VerifyToken(Resource):
    @auth_ns.doc(description='验证Token有效性')
    def get(self):
        """验证Token有效性"""
        token = request.cookies.get('auth_token')
        if not token:
            return {'authenticated': False}, 401

        try:
            data = jwt.decode(token, current_app.config['SECRET_KEY'], algorithms=["HS256"])
            return {
                'authenticated': True,
                'user': {
                    'uid': data['uid'],
                    'username': data['username'],
                    'role': data['role']
                }
            }
        except jwt.ExpiredSignatureError:
            return {'authenticated': False, 'message': 'Token已过期'}, 401
        except jwt.InvalidTokenError:
            return {'authenticated': False, 'message': '无效Token'}, 401


@auth_ns.route('/logout')
class Logout(Resource):
    @auth_ns.doc(description='用户登出')
    def post(self):
        """用户登出接口"""
        return logout_user()


@auth_ns.route('/verify-cf')
class VerifyCF(Resource):
    @auth_ns.doc(description='验证Cloudflare Turnstile令牌')
    @auth_ns.expect(cf_verify_model)
    def post(self):
        """验证Cloudflare Turnstile令牌"""
        data = request.get_json()
        if not data:
            return {"success": False, "error": "请求数据必须是 JSON 格式"}, 400

        return check_cf_token(data)


@auth_ns.route('/send-email-code')
class SendEmailCode(Resource):
    @auth_ns.doc(description='发送邮箱验证码')
    @auth_ns.expect(email_code_model)
    def post(self):
        """发送邮箱验证码接口"""
        data = request.get_json()
        email = data.get("email")

        if not email:
            return {"success": False, "message": "邮箱不能为空"}, 400

        code = generate_code()
        if send_verification_email(email, code):
            save_code_to_redis(email, code)
            return {"success": True, "message": "验证码已发送"}
        else:
            return {"success": False, "message": "邮件发送失败"}, 500


@auth_ns.route('/verify-email-code')
class VerifyEmailCode(Resource):
    @auth_ns.doc(description='验证邮箱验证码')
    @auth_ns.expect(verify_code_model)
    def post(self):
        """验证邮箱验证码接口"""
        data = request.get_json()
        email = data.get("email")
        user_code = data.get("code")

        if not all([email, user_code]):
            return {"success": False, "message": "参数不完整"}, 400

        return verify_email_code(email, user_code)
