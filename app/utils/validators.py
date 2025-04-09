import os
import re


def validate_credentials(username, password):
    """验证用户名和密码格式"""
    if not all([username, password]):
        return {'valid': False, 'message': '用户名和密码不能为空'}

    if not re.match(r'^[a-zA-Z0-9]{5,12}$', username):
        return {'valid': False, 'message': '用户名必须是5-12位字母数字组合'}

    if not re.match(r'^[a-zA-Z0-9]{6,18}$', password):
        return {'valid': False, 'message': '密码必须是6-18位字母数字组合'}

    return {'valid': True, 'message': '验证通过'}


from config import Config


def is_safe_filename(filename):
    """检查文件名是否安全（防止路径遍历攻击）"""
    allowed_extensions = Config.ALLOWED_AVATAR_EXTENSIONS

    return (
            not filename.startswith(('.', '/')) and
            '..' not in filename and
            os.path.splitext(filename)[1][1:].lower() in allowed_extensions
    )
