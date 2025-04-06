from flask import Blueprint, request, jsonify, current_app
from ..services.first_blood_service import get_first_blood
first_blood_bp = Blueprint('first_blood', __name__)


@first_blood_bp.route('/firstblood', methods=['POST'])
def first_blood():
    """题目列表接口"""
    # 获取请求数据
    data = request.get_json()
    if not data:
        return jsonify({"success": False, "message": "请求数据必须是JSON格式"}), 400
    # contest_id
    contest_id = data.get('contest_id','')

    return get_first_blood(contest_id)
