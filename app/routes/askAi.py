from flask import Blueprint, request, jsonify, g
from flask import Response, stream_with_context
from ..services.ollama_service import generate_completion_stream, judge_question
from ..utils.role_utils import optional_login

askAi_bp = Blueprint('askAi', __name__)


@askAi_bp.route('/askAi-msg', methods=['POST'])
def stream_to_ai():
    try:
        data = request.get_json()
        prompt = data.get('prompt')

        if not prompt:
            return jsonify({"success": False, "message": "内容不能为空"}), 400

        # 流式响应
        return Response(
            stream_with_context(generate_completion_stream(prompt)),
            mimetype='text/event-stream',
            headers={
                'Cache-Control': 'no-cache',
                'Connection': 'keep-alive',
                'X-Accel-Buffering': 'no'  # 禁用Nginx缓冲
            }
        )

    except Exception as e:
        return jsonify({"success": False, "message": str(e)}), 500


@askAi_bp.route('/askAi-question', methods=['POST'])
@optional_login
def judge_to_ai():
    try:
        # data = request.get_json()
        # prompt = data.get('prompt', None)
        # question = str(data.get('question', None))
        # user_id = getattr(g, 'current_user_id', None)

        prompt = request.form.get('prompt', None)
        question = request.form.get('question', None)
        user_id = getattr(g, 'current_user_id', None)

        return judge_question(prompt, question, user_id)

    except Exception as e:
        return jsonify({"success": False, "message": str(e)}), 500
