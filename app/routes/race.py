from flask import Blueprint, request, jsonify, g
from ..services.race_info_service import get_race_info, get_race_list
from ..utils.role_utils import optional_login

race_bp = Blueprint('race_info', __name__)


@race_bp.route('/race-info', methods=['GET'])
@optional_login
def race_info():
    """题目列表接口"""
    # 获取请求数据
    data = request.get_json()
    if not data:
        return jsonify({"success": False, "message": "请求数据必须是JSON格式"}), 400

    user_id = getattr(g, 'current_user_id', None)
    race_uid = data.get('uid', '')

    return get_race_info(race_uid, user_id)


@race_bp.route('/race-list', methods=['GET'])
def race_list():
    return get_race_list()