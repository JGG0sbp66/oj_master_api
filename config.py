# config.py
import os
from datetime import timedelta


class Config:
    # 安全密钥配置
    SECRET_KEY = os.environ.get('SECRET_KEY') or os.urandom(24).hex()  # 优先从环境变量读取
    JWT_ALGORITHM = "HS256"
    JWT_EXPIRATION = timedelta(hours=4)  # Token有效期

    # 数据库配置
    SQLALCHEMY_DATABASE_URI = 'mysql+pymysql://root:@localhost:3308/reborn_oj_master'
    SQLALCHEMY_TRACK_MODIFICATIONS = False

    # 会话配置
    PERMANENT_SESSION_LIFETIME = timedelta(minutes=30)

    # Turnstile 验证配置
    TURNSTILE_SECRET_KEY = "0x4AAAAAABC_Oa6dJZB8d7Ql7PRLdDli0Vc"

    # 角色权限定义
    ROLES = {
        'user': 1,
        'admin': 2
    }

    # 头像配置
    AVATAR_UPLOAD_DIR = os.path.join(os.path.dirname(__file__), 'app', 'user_img', 'avatar')
    ALLOWED_AVATAR_EXTENSIONS = {'png', 'jpg', 'jpeg', 'gif'}
    MAX_AVATAR_SIZE = 2 * 1024 * 1024  # 2MB
    DEFAULT_AVATAR = 'default.png'
