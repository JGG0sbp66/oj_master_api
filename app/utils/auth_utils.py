# auth_utils.py
from datetime import datetime
import jwt
from flask import current_app


def generate_token(uid, username, role):
    """生成JWT Token"""
    payload = {
        "uid": uid,
        "username": username,
        "role": role,
        "exp": datetime.now() + current_app.config['JWT_EXPIRATION']
    }
    return jwt.encode(
        payload,
        current_app.config['SECRET_KEY'],
        algorithm=current_app.config['JWT_ALGORITHM']
    )


def verify_token(token):
    """验证Token"""
    try:
        return jwt.decode(
            token,
            current_app.config['SECRET_KEY'],
            algorithms=[current_app.config['JWT_ALGORITHM']]
        )
    except (jwt.ExpiredSignatureError, jwt.InvalidTokenError) as e:
        current_app.logger.warning(f"Token验证失败: {str(e)}")
        return None
