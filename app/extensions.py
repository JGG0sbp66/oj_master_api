import os

from flask_sqlalchemy import SQLAlchemy
import redis
from config import Config

# 数据库扩展
db = SQLAlchemy()


# Redis 扩展
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
                max_connections=20,
                decode_responses=True
            )
        )

    def __getattr__(self, name):
        return getattr(self.redis, name)


redis_wrapper = RedisWrapper()

# Celery 扩展
from celery import Celery

celery = Celery(
    __name__,
    broker=Config.broker_url,
    backend=Config.result_backend
)
celery.conf.update(
    beat_schedule_filename=os.path.join(Config.beat_schedule_dir, 'celerybeat-schedule'),
    imports=['app.utils.race_task'],
)
