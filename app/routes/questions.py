from flask import Blueprint, request, jsonify, current_app
from ..services.questoin_service import get_questions

questions_bp = Blueprint('questions', __name__)


@questions_bp.route('/questions', methods=['POST'])
def question_list():
    """题目列表接口"""
    # 获取请求数据
    data = request.get_json()
    if not data:
        return jsonify({"success": False, "message": "请求数据必须是JSON格式"}), 400
    # page, category, topic, input
    page = data.get('page', '')
    category = data.get('category', '')
    topic = data.get('topic', '')
    textinput = data.get('input', '')
    a = 1
    return get_questions(page, category, topic, textinput)
