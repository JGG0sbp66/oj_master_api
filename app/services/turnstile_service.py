import requests
from flask import jsonify
from flask import current_app as app


def check_cf_token(token_data):
    token = token_data.get('cfToken')
    if not token:
        return jsonify({"success": False, "error": "cfToken不能为空"}), 400

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
        return jsonify({"success": True, "message": "验证成功"})
    else:
        return jsonify({
            "success": False,
            "error": "cfToken验证失败",
            "codes": result.get("error-codes", [])
        }), 400
