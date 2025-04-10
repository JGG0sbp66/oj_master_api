from flask import Blueprint, request, jsonify, current_app, g
from ..services.questoin_service import get_questions, get_question_detail
from ..utils.role_utils import optional_login

questions_bp = Blueprint('questions', __name__)


@questions_bp.route('/questions', methods=['POST'])
@optional_login
def question_list():
    try:
        data = request.get_json()
        user_id = getattr(g, 'current_user_id', None)  # 关键获取点

        result = get_questions(
            page=int(data.get('page', 1)),
            category=str(data.get('category', '')).strip(),
            topic=str(data.get('topic', '')).strip(),
            textinput=str(data.get('input', '')).strip(),
            user_id=user_id  # 直接传递
        )

        return jsonify({
            "success": True,
            "questions": result.get('questions', []),
            "total_page": result.get('total_page', 1),
            "total_count": result.get('total_count', 0)
        })
    except ValueError:
        return jsonify({"success": False, "message": "参数类型错误"}), 400


@questions_bp.route('/question-detail', methods=['POST'])
def question_detail():
    try:
        data = request.get_json()
        if not data:
            return jsonify({"success": False, "message": "请求数据必须是JSON格式"}), 400

        question_id = data.get('uid', '')
        result = get_question_detail(int(question_id))
        return jsonify({
            "success": True,
            "question_detail": result
        })

    except ValueError:
        return jsonify({"success": False, "message": "参数类型错误"}), 400