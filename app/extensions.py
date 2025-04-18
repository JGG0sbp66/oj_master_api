# extensions.py
from flask_sqlalchemy import SQLAlchemy

db = SQLAlchemy()

import redis


class RedisWrapper:
    def __init__(self, app=None):
        self.redis = None
        if app is not None:
            self.init_app(app)

    def init_app(self, app):
        self.redis = redis.Redis(
            connection_pool=redis.ConnectionPool(
                host=app.config['REDIS_CONFIG']['host'],
                port=app.config['REDIS_CONFIG']['port'],
                db=app.config['REDIS_CONFIG']['db'],
                max_connections=20,  # 连接池大小
                decode_responses=True  # 自动解码
            )
        )

    def __getattr__(self, name):
        return getattr(self.redis, name)


# 创建扩展实例
redis_wrapper = RedisWrapper()
from celery import Celery

celery = Celery(__name__, broker='redis://localhost:6379/0')
