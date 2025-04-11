# app/__init__.py
from flask import Flask
from flask_cors import CORS
from .extensions import db
import logging
from logging.handlers import RotatingFileHandler


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

    # 延迟导入蓝图
    from .routes.auth import auth_bp
    from .routes.questions import questions_bp
    from .routes.race import race_bp
    from .routes.admin_routes.admin_api_test import admin_test_bp
    from .routes.user_routes.avatar import avatar_bp
    from .routes.askAi import askAi_bp

    app.register_blueprint(auth_bp, url_prefix='/api')
    app.register_blueprint(questions_bp, url_prefix='/api')
    app.register_blueprint(race_bp, url_prefix='/api')
    app.register_blueprint(admin_test_bp, url_prefix='/api')
    app.register_blueprint(avatar_bp, url_prefix='/api')
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
