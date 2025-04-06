from flask import Blueprint, request, jsonify
from ..services.race_info_service import get_race_info, get_race_list
race_bp = Blueprint('race_info', __name__)


@race_bp.route('/raceinfo', methods=['POST'])
def race_info():
    """题目列表接口"""
    # 获取请求数据
    data = request.get_json()
    if not data:
        return jsonify({"success": False, "message": "请求数据必须是JSON格式"}), 400
    # uid
    uid = data.get('uid', '')

    return get_race_info(uid)


@race_bp.route('/race-list', methods=['GET'])
def race_list():
    # 获取请求数据
    data = request.get_json()
    if not data:
        return jsonify({"success": False, "message": "请求数据必须是JSON格式"}), 400

    # page, limit
    page = data.get('page', 1)
    limit = data.get('limit', 4)

    return get_race_list(page, limit)
