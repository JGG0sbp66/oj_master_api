import smtplib
from email.mime.text import MIMEText
from config import Config
import requests, random, string
from flask import current_app as app, current_app
from email.mime.multipart import MIMEMultipart

from .. import redis_wrapper
from ..utils.validators import render_email_template


def check_cf_token(token_data):
    token = token_data.get('cfToken')
    if not token:
        return {"success": False, "error": "cfToken不能为空"}, 400

    # 使用 current_app 获取配置
    response = requests.post(
        "https://challenges.cloudflare.com/turnstile/v0/siteverify",
        data={
            "secret": app.config['TURNSTILE_SECRET_KEY'],
            "response": token
        }
    )
    result = response.json()

    if result.get("success"):
        return {"success": True, "message": "验证成功"}, 200
    else:
        return {
            "success": False,
            "error": "cfToken验证失败",
            "codes": result.get("error-codes", [])
        }, 400


# 生成随机验证码
def generate_code(length=6):
    return ''.join(random.choices(string.digits, k=length))


SMTP_CONFIG = Config.SMTP_CONFIG


# 发送邮件函数
def send_verification_email(to_email, code):
    """发送验证码邮件（使用模板）"""
    sender = SMTP_CONFIG["user"]

    try:
        html_content = render_email_template("email.html", verification_code=code)

        msg = MIMEMultipart('alternative')
        msg['From'] = sender
        msg['To'] = to_email
        msg['Subject'] = "您的验证码 - 请及时查收"

        msg.attach(MIMEText(html_content, 'html'))
        msg.attach(MIMEText(f"您的验证码是：{code}，5分钟内有效。", 'plain'))

        with smtplib.SMTP_SSL(SMTP_CONFIG["host"], SMTP_CONFIG["port"]) as server:
            server.login(sender, SMTP_CONFIG["password"])
            server.sendmail(sender, [to_email], msg.as_string())

        app.logger.info(f"邮件发送成功: {to_email}")
        return True

    except Exception as e:
        app.logger.error(f"邮件发送失败到 {to_email}: {str(e)}")
        return False


# 存储验证码到Redis（设置5分钟过期）
def save_code_to_redis(email, code):
    redis_wrapper.setex(f"verify_code:{email}", 300, code)


def verify_email_code(email, user_code):
    try:
        stored_code = redis_wrapper.get(f"verify_code:{email}")

        if stored_code == user_code:
            redis_wrapper.delete(f"verify_code:{email}")
            return {"success": True, "message": "验证码正确"}, 200
        return {"success": False, "message": "验证码错误"}, 400
    except Exception as e:
        current_app.logger.error(f"验证码校验异常: {e}")
        return {"success": False, "message": "服务器错误"}, 500
