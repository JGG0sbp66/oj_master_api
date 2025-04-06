from flask import Blueprint, request, jsonify

from app.services.turnstile_service import check_cf_token

turnstile_bp = Blueprint('turnstile', __name__)


@turnstile_bp.route('/verify-cf', methods=['POST'])
def verify():
    data = request.get_json()
    if not data:
        return jsonify({"success": False, "error": "请求数据必须是 JSON 格式"}), 400

    return check_cf_token(data)
