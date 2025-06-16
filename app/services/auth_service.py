from datetime import timedelta, datetime
import bcrypt
import requests
from flask import make_response
from ..models import User
from ..extensions import db
from ..utils.auth_utils import generate_token


def register_user(username, password, email, email_code, cf_token):
    # 验证 Cloudflare Turnstile
    try:
        response = requests.post(
            "http://localhost:5000/api/verify-cf",
            json={"cfToken": cf_token},
            headers={"Content-Type": "application/json"}
        )
        Cloudflare_Turnstile_result = response.json()
    except Exception as e:
        return {
            'success': False,
            'message': f'验证码服务异常: {str(e)}'
        }, 500

    if not Cloudflare_Turnstile_result.get('success'):
        return {
            'success': False,
            'message': '验证码校验失败'
        }, 403

    # 验证邮箱验证码
    try:
        response = requests.post(
            "http://localhost:5000/api/verify-email-code",
            json={"email": email, "code": email_code},
            headers={"Content-Type": "application/json"}
        )
        email_code_result = response.json()
    except Exception as e:
        return {
            'success': False,
            'message': f'验证码服务异常: {str(e)}'
        }, 500

    if not email_code_result.get('success'):
        return {
            'success': False,
            'message': '邮箱验证码错误'
        }, 403

    # 检查用户名是否已存在
    if User.query.filter_by(username=username).first():
        return {
            'success': False,
            'message': '用户名已存在'
        }, 400

    # 密码哈希处理
    try:
        hashed_password = bcrypt.hashpw(password.encode('utf-8'), bcrypt.gensalt())
    except Exception as e:
        return {
            'success': False,
            'message': f'密码加密失败: {str(e)}'
        }, 500

    # 创建新用户
    try:
        new_user = User(username=username, password=hashed_password.decode('utf-8'), email=email)
        db.session.add(new_user)
        db.session.commit()
        return {
            'success': True,
            'message': '注册成功!'
        }
    except Exception as e:
        db.session.rollback()
        return {
            'success': False,
            'message': f'注册失败: {str(e)}'
        }, 500


def login_user(username, password):
    user = User.query.filter_by(username=username).first()
    if not user:
        return {'success': False, 'message': '用户名或密码错误'}, 401

    # 检查用户是否被封禁
    if user.is_banned:
        # 检查是否是临时封禁
        if user.ban_end_time and user.ban_end_time > datetime.now():
            return {
                'success': False,
                'message': f'账号已被封禁，原因: {user.ban_reason}。封禁截止时间: {user.ban_end_time.strftime("%Y-%m-%d %H:%M:%S")}'
            }, 403
        # 永久封禁
        elif user.ban_end_time is None:
            return {
                'success': False,
                'message': f'账号已被永久封禁，原因: {user.ban_reason}'
            }, 403
        # 封禁已过期但标记未清除的情况
        else:
            # 可以在这里自动解除封禁状态
            user.is_banned = False
            db.session.commit()

    try:
        if bcrypt.checkpw(password.encode('utf-8'), user.password.encode('utf-8')):
            # 封禁检查通过后才生成token
            token = generate_token(user.uid, user.username, user.role)

            response_data = {
                'success': True,
                'message': '登录成功',
                'user': {
                    'uid': user.uid,
                    'username': user.username,
                    'role': user.role,
                    'auth_token': token,
                    'is_banned': False  # 明确返回封禁状态
                }
            }

            response = make_response(response_data)
            response.set_cookie(
                'auth_token',
                value=token,
                max_age=int(timedelta(days=7).total_seconds()),
                path='/',
                secure=False,
                httponly=True,
                samesite='Lax'
            )
            return response
        else:
            return {'success': False, 'message': '用户名或密码错误'}, 401
    except Exception as e:
        return {'success': False, 'message': f'登录失败: {str(e)}'}, 500


def repassword_user(username, email, email_code, new_password):
    # 验证邮箱验证码
    try:
        response = requests.post(
            "http://localhost:5000/api/verify-email-code",
            json={"email": email, "code": email_code},
            headers={"Content-Type": "application/json"}
        )
        email_code_result = response.json()
    except Exception as e:
        return {
            'success': False,
            'message': f'验证码服务异常: {str(e)}'
        }, 500

    if not email_code_result.get('success'):
        return {
            'success': False,
            'message': '邮箱验证码错误'
        }, 403

    # 检查用户名是否存在
    user = User.query.filter_by(username=username).first()
    if not user:
        return {
            'success': False,
            'message': '用户名不存在，请先注册'
        }, 400

    # 验证邮箱是否匹配
    if user.email != email:
        return {
            'success': False,
            'message': '邮箱与用户名不匹配'
        }, 400

    # 密码哈希处理
    try:
        hashed_password = bcrypt.hashpw(new_password.encode('utf-8'), bcrypt.gensalt())
    except Exception as e:
        return {
            'success': False,
            'message': f'密码加密失败: {str(e)}'
        }, 500

    # 更新密码
    try:
        user.password = hashed_password.decode('utf-8')
        db.session.commit()
        return {
            'success': True,
            'message': '密码重置成功!'
        }
    except Exception as e:
        db.session.rollback()
        return {
            'success': False,
            'message': f'密码重置失败: {str(e)}'
        }, 500


def logout_user():
    """处理用户退出登录"""
    # 创建响应对象
    response_data = {
        'success': True,
        'message': '退出登录成功'
    }
    response = make_response(response_data)

    # 清除 auth_token Cookie（必须与登录时的设置完全一致）
    response.delete_cookie(
        'auth_token',
        path='/',
        secure=False,
        httponly=True,
        samesite='Lax'
    )

    return response
