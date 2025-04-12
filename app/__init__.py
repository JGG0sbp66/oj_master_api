# app/__init__.py
from flask import Flask
from flask_cors import CORS
from flask_restx import Api
from .extensions import db
import logging
from logging.handlers import RotatingFileHandler

api = Api(version="1.0", title="Reborn OJ Master API", description="OJ Master API文档", doc="/oj-master/api")

def create_app(config_class='config.Config'):
    app = Flask(__name__)
    app.config.from_object(config_class)

    # 初始化扩展
    db.init_app(app)
    CORS(
        app,
        resources={
            r"/api/*": {
                "origins": ["http://localhost:5173"],  # 明确指定前端地址
                "supports_credentials": True,  # 允许带凭证
                "allow_headers": ["Content-Type", "Authorization"],
                "methods": ["GET", "POST", "OPTIONS"]
            }
        }
    )

    # 初始化扩展
    api.init_app(app)

    # 延迟导入蓝图
    from .routes.auth import auth_bp
    from .routes.questions import questions_bp
    from .routes.race import race_bp
    from .routes.admin_routes.admin_api_test import admin_ns
    from .routes.user_routes.user_info import user_info_bp
    from .routes.askAi import askAi_bp

    app.register_blueprint(auth_bp, url_prefix='/api')
    app.register_blueprint(questions_bp, url_prefix='/api')
    app.register_blueprint(race_bp, url_prefix='/api')
    api.add_namespace(admin_ns)
    app.register_blueprint(user_info_bp, url_prefix='/api')
    app.register_blueprint(askAi_bp, url_prefix='/api')

    app.permanent_session_lifetime = app.config['PERMANENT_SESSION_LIFETIME']

    # 配置日志
    handler = RotatingFileHandler('app.log', maxBytes=10000, backupCount=3, encoding='utf-8')
    handler.setFormatter(logging.Formatter(
        '[%(asctime)s] %(levelname)s in %(module)s: %(message)s'
    ))
    app.logger.addHandler(handler)
    app.logger.setLevel(logging.INFO)

    return app
