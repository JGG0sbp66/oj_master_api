from functools import wraps
from flask import jsonify, request
import jwt
from flask import current_app


def role_required(*roles):
    def decorator(f):
        @wraps(f)
        def decorated_function(*args, **kwargs):
            token = request.cookies.get('auth_token')
            if not token:
                return jsonify({'success': False, 'message': '请先登录'}), 401

            try:
                data = jwt.decode(token, current_app.config['SECRET_KEY'], algorithms=["HS256"])
                if data.get('role') not in roles:
                    return jsonify({'success': False, 'message': '权限不足'}), 403
            except jwt.ExpiredSignatureError:
                return jsonify({'success': False, 'message': 'Token已过期'}), 401
            except jwt.InvalidTokenError:
                return jsonify({'success': False, 'message': '无效Token'}), 401

            return f(*args, **kwargs)

        return decorated_function

    return decorator
