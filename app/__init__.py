# app/__init__.py
import json
import os

from flask import Flask
from flask_cors import CORS
from flask_restx import Api
from .extensions import db, redis_wrapper
import logging
from logging.handlers import RotatingFileHandler
from .extensions import celery

api = Api(version="1.0", title="Reborn OJ Master API", description="OJ Master API文档", doc="/oj-master/api")


def create_app(config_class='config.Config'):
    app = Flask(__name__)
    app.config.from_object(config_class)
    celery.conf.update(app.config)

    @api.representation('application/json')
    def output_json(data, code, headers=None):
        """确保JSON响应禁用ASCII转义并保留状态码"""
        resp = app.make_response(json.dumps(data, ensure_ascii=False))
        resp.status_code = code  # 关键修复：设置状态码
        resp.headers.extend(headers or {})
        resp.content_type = 'application/json; charset=utf-8'
        return resp

    # 初始化Redis
    redis_wrapper.init_app(app)

    # 初始化数据库
    db.init_app(app)

    CORS(
        app,
        resources={
            r"/api/*": {
                "origins": ["http://localhost:5173"],  # 明确指定前端地址
                "supports_credentials": True,  # 允许带凭证
                "allow_headers": ["Content-Type", "Authorization"],
                "methods": ["GET", "POST", "PUT", "DELETE", "OPTIONS"]
            }
        }
    )

    # 初始化扩展
    api.init_app(app)

    # 延迟导入蓝图
    from .routes.auth import auth_ns
    from .routes.questions import questions_ns
    from .routes.race import race_ns
    from .routes.admin_routes.admin_race import admin_ns
    from .routes.admin_routes.admin_question import admin_questions_ns
    from .routes.user_routes.user_info import user_info_ns
    from .routes.askAi import ai_ns
    from .routes.panel import panel_ns
    from .routes.admin_routes.admin_userManage import admin_userManage
    from .routes.judge import judge_ns

    api.add_namespace(auth_ns)
    api.add_namespace(questions_ns)
    api.add_namespace(race_ns)
    api.add_namespace(admin_ns)
    api.add_namespace(admin_questions_ns)
    api.add_namespace(user_info_ns)
    api.add_namespace(ai_ns)
    api.add_namespace(panel_ns)
    api.add_namespace(admin_userManage)
    api.add_namespace(judge_ns)

    app.permanent_session_lifetime = app.config['PERMANENT_SESSION_LIFETIME']

    # 配置日志
    os.makedirs(app.config['LOG_DIR'], exist_ok=True)
    handler = RotatingFileHandler(
        app.config['LOG_FILE'],
        maxBytes=app.config['LOG_MAX_BYTES'],
        backupCount=app.config['LOG_BACKUP_COUNT'],
        encoding='utf-8'
    )
    handler.setFormatter(logging.Formatter(app.config['LOG_FORMAT']))
    app.logger.addHandler(handler)
    app.logger.setLevel(app.config['LOG_LEVEL'])

    return app
