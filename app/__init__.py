# app/__init__.py
from flask import Flask
from flask_cors import CORS
from .extensions import db


def create_app(config_class='config.Config'):  # 注意这里改为 'config.Config'
    app = Flask(__name__)
    app.config.from_object(config_class)  # 确保这行正确执行

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
    from .routes.turnstile import turnstile_bp
    from app.routes.questions import questions_bp

    app.register_blueprint(auth_bp, url_prefix='/api')
    app.register_blueprint(turnstile_bp, url_prefix='/api')
    app.register_blueprint(questions_bp, url_prefix='/api')

    app.permanent_session_lifetime = app.config['PERMANENT_SESSION_LIFETIME']

    return app
