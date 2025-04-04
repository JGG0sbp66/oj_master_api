from flask import Blueprint, request, jsonify
import requests
from flask import current_app as app

turnstile_bp = Blueprint('turnstile', __name__)


@turnstile_bp.route('/verify-cf', methods=['POST'])
def verify():
    data = request.get_json()
    if not data:
        return jsonify({"success": False, "error": "请求数据必须是 JSON 格式"}), 400

    token = data.get('cfToken')
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
