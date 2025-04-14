import re, os


def validate_credentials(username, password, email):
    """验证用户名、密码和邮箱格式"""
    if not all([username, password, email]):
        return {'valid': False, 'message': '用户名、密码和邮箱不能为空'}

    if not re.match(r'^[a-zA-Z0-9]{5,12}$', username):
        return {'valid': False, 'message': '用户名必须是5-12位字母数字组合'}

    if not re.match(r'^[a-zA-Z0-9]{6,18}$', password):
        return {'valid': False, 'message': '密码必须是6-18位字母数字组合'}

    if not re.match(r'^[a-zA-Z0-9_.+-]+@[a-zA-Z0-9-]+\.[a-zA-Z0-9-.]+$', email):
        return {'valid': False, 'message': '邮箱格式不正确'}

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


from pathlib import Path
from string import Template
import datetime


def render_email_template(template_name: str, **kwargs) -> str:
    """
    渲染邮件HTML模板
    :param template_name: 模板文件名（位于templates/email目录）
    :param kwargs: 模板变量
    :return: 渲染后的HTML字符串
    """
    template_path = Path(__file__).parent / template_name
    with open(template_path, "r", encoding="utf-8") as f:
        template = Template(f.read())

    # 添加默认变量
    defaults = {
        "current_year": datetime.datetime.now().year,
        "app_name": "OJ Master"
    }
    defaults.update(kwargs)

    return template.substitute(defaults)


class BusinessException(Exception):
    def __init__(self, message, status_code=400):
        super().__init__(message)
        self.status_code = status_code
        self.message = message
