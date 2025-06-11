# config.py
import logging
import os
from datetime import timedelta
from dotenv import load_dotenv

env_path = os.path.join(os.path.dirname(__file__), 'data', '.env')
load_dotenv(dotenv_path=env_path)


class Config:
    JSON_AS_ASCII = False
    JSONIFY_PRETTYPRINT_REGULAR = True
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
    TURNSTILE_SECRET_KEY = os.environ.get('TURNSTILE_SECRET_KEY')

    # 角色权限定义
    ROLES = {
        'user': 1,
        'admin': 2
    }

    # 头像配置
    AVATAR_UPLOAD_DIR = os.path.join(os.path.dirname(__file__), 'data', 'user_img', 'avatar')
    ALLOWED_AVATAR_EXTENSIONS = {'png', 'jpg', 'jpeg', 'gif'}
    MAX_AVATAR_SIZE = 2 * 1024 * 1024  # 2MB
    DEFAULT_AVATAR = 'default.png'

    # ollama 路径配置
    OLLAMA_ADDRESS = "http://localhost:11434/api"

    # SMTP 和 Redis 配置
    SMTP_CONFIG = {
        "host": "smtp.163.com",
        "port": 465,
        "user": "oj_master@163.com",
        "password": os.environ.get('SMTP_PASSWORD')
    }
    REDIS_CONFIG = {
        "host": "localhost",
        "port": 6379,
        "db": 0
    }

    # deepseek api
    deepseek_api_key = os.environ.get('DEEPSEEK_API_KEY')

    # 上传测试用例配置
    TESTCASE_UPLOAD_DIR = os.path.join(os.path.dirname(__file__), 'data', 'test_case', 'tmp')
    ALLOWED_TESTCASE_EXTENSIONS = {'zip'}
    MAX_TESTCASE_SIZE = 16 * 1024 * 1024  # 16MB

    # 日志配置
    LOG_DIR = os.path.join(os.path.dirname(__file__), 'data', 'logs')
    LOG_FILE = os.path.join(LOG_DIR, "app.log")
    LOG_MAX_BYTES = 10000
    LOG_BACKUP_COUNT = 3
    LOG_LEVEL = logging.INFO
    LOG_FORMAT = '[%(asctime)s] %(levelname)s in %(module)s: %(message)s'

    # Celery 配置
    CELERY_BROKER_URL = 'redis://localhost:6379/0'
    CELERY_RESULT_BACKEND = 'redis://localhost:6379/1'
    CELERYBEAT_SCHEDULE_DIR = os.path.join(os.path.dirname(__file__), 'data', 'celery')
