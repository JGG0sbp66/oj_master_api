from flask import Blueprint, request, jsonify, g
from ..services.race_info_service import get_race_info, get_race_list, get_race_rank
from ..utils.role_utils import optional_login

race_bp = Blueprint('race_info', __name__)


@race_bp.route('/race-info', methods=['POST'])
@optional_login
def race_info():
    try:
        data = request.get_json()
        user_id = getattr(g, 'current_user_id', None)
        return get_race_info(race_id=int(data.get('uid', 1)), user_id=user_id)

    except ValueError:
        return jsonify({"success": False, "message": "参数类型错误"}), 400


@race_bp.route('/race-list', methods=['POST'])
def race_list():
    return get_race_list()


@race_bp.route('/race-rank', methods=['POST'])
def race_rank():
    data = request.get_json()
    if not data:
        return jsonify({"success": False, "message": "请求数据必须是JSON格式"}), 400
    race_uid = data.get('uid', '')

    return get_race_rank(race_uid)
