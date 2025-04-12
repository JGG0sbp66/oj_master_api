from functools import wraps
from flask import jsonify, request, g
import jwt
from flask import current_app


def role_required(*roles):
    def decorator(f):
        @wraps(f)
        def decorated_function(*args, **kwargs):
            token = request.cookies.get('auth_token')
            if not token:
                return {'success': False, 'message': '请先登录'}, 401

            try:
                data = jwt.decode(token, current_app.config['SECRET_KEY'], algorithms=["HS256"])
                if data.get('role') not in roles:
                    return {'success': False, 'message': '权限不足'}, 403
            except jwt.ExpiredSignatureError:
                return {'success': False, 'message': 'Token已过期'}, 401
            except jwt.InvalidTokenError:
                return {'success': False, 'message': '无效Token'}, 401

            return f(*args, **kwargs)

        return decorated_function

    return decorator


def optional_login(f):
    """
        可选登录装饰器。
        用于在 Flask 视图函数中检查用户的登录状态（通过 Cookie 中的 auth_token）。
        如果用户已登录（即 auth_token 有效），则将用户 ID 存储在 g.current_user_id 中；
        如果用户未登录或 Token 无效，则保持游客状态，不影响正常访问。
        """

    @wraps(f)
    def decorated(*args, **kwargs):
        # 清除可能存在的旧用户ID
        if hasattr(g, 'current_user_id'):
            del g.current_user_id

        # 统一使用get()方法读取Cookie
        token = request.cookies.get('auth_token')
        if token:
            try:
                data = jwt.decode(token, current_app.config['SECRET_KEY'], algorithms=["HS256"])
                g.current_user_id = data['uid']  # 确保使用小写uid
            except jwt.PyJWTError:
                pass  # 保持游客状态
        return f(*args, **kwargs)

    return decorated
