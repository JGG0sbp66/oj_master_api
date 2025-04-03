from datetime import timedelta

import bcrypt
import requests
from flask import jsonify, session

from ..models import User
from ..extensions import db


def register_user(username, password, cf_token):
    # 验证 Cloudflare Turnstile
    try:
        response = requests.post(
            "http://localhost:5000/api/verify-cf",
            json={"cfToken": cf_token},
            headers={"Content-Type": "application/json"}
        )
        result = response.json()
    except Exception as e:
        return jsonify({
            'success': False,
            'message': f'验证码服务异常: {str(e)}'
        }), 500

    if not result.get('success'):
        return jsonify({
            'success': False,
            'message': '验证码校验失败'
        }), 403

    # 检查用户名是否已存在
    if User.query.filter_by(username=username).first():
        return jsonify({
            'success': False,
            'message': '用户名已存在'
        }), 400

    # 密码哈希处理
    try:
        hashed_password = bcrypt.hashpw(password.encode('utf-8'), bcrypt.gensalt())
    except Exception as e:
        return jsonify({
            'success': False,
            'message': f'密码加密失败: {str(e)}'
        }), 500

    # 创建新用户
    try:
        new_user = User(username=username, password=hashed_password.decode('utf-8'))
        db.session.add(new_user)
        db.session.commit()
        return jsonify({
            'success': True,
            'message': '注册成功!'
        })
    except Exception as e:
        db.session.rollback()
        return jsonify({
            'success': False,
            'message': f'注册失败: {str(e)}'
        }), 500

def login_user(username, password):
    user = User.query.filter_by(username=username).first()

    if not user:
        return jsonify({
            'success': False,
            'message': '用户名或密码错误'
        }), 401

    try:
        if bcrypt.checkpw(password.encode('utf-8'), user.password.encode('utf-8')):
            session.permanent = True
            session['username'] = username

            response = jsonify({
                'success': True,
                'message': '登录成功'
            })

            response.set_cookie(
                'username',
                value=username,
                max_age=int(timedelta(days=7).total_seconds()),  # 将 float 转换为 int
                path='/',
                secure=False,
                httponly=True
            )

            return response
        else:
            return jsonify({
                'success': False,
                'message': '用户名或密码错误'
            }), 401
    except Exception as e:
        return jsonify({
            'success': False,
            'message': f'密码验证失败: {str(e)}'
        }), 500