from flask_restx import Resource, fields, reqparse
from flask import request, Response, stream_with_context, g
from app import api  # 从主模块导入api实例
from app.services.ollama_service import generate_completion_stream, generate_completion, explain2, \
    judge_prompt, question_start, question_end
from app.services.questoin_service import judge_question
from app.utils.role_utils import optional_login

# 创建 AI 相关接口命名空间
ai_ns = api.namespace('AI', description='AI 相关接口', path='/api')

# 模型定义
ai_message_model = api.model('AIMessage', {
    'prompt': fields.String(required=True, description='用户输入的提示词')
})

ai_judge_parser = reqparse.RequestParser()
ai_judge_parser.add_argument('prompt', type=str, required=False, help='用户输入的代码', location='form')
ai_judge_parser.add_argument('question', type=str, required=True, help='要评判的问题', location='form')
ai_judge_parser.add_argument('question_uid', type=str, required=False, help='问题唯一标识', location='form')
ai_judge_parser.add_argument('race_id', type=int, required=False, help='比赛ID', location='form')


@ai_ns.route('/askAi-msg')
class AIMessage(Resource):
    @ai_ns.doc(description='与AI对话（流式响应）')
    @ai_ns.expect(ai_message_model)
    def post(self):
        """
        与AI对话（流式响应）

        返回流式响应，用于实时显示AI生成的内容
        """
        try:
            data = request.get_json()
            prompt = data.get('prompt')

            if not prompt:
                return {
                    "success": False,
                    "message": "内容不能为空"
                }, 400

            # 流式响应
            return Response(
                stream_with_context(generate_completion_stream(prompt, model="gemma3:4b")),
                mimetype='text/event-stream',
                headers={
                    'Cache-Control': 'no-cache',
                    'Connection': 'keep-alive',
                    'X-Accel-Buffering': 'no'  # 禁用Nginx缓冲
                }
            )

        except Exception as e:
            return {
                "success": False,
                "message": str(e)
            }, 500


@ai_ns.route('/askAi-question')
class AIJudge(Resource):
    @ai_ns.doc(security='Bearer', description='AI评判问题')
    @ai_ns.expect(ai_judge_parser)
    @optional_login
    def post(self):
        """
        AI评判问题

        使用AI对问题进行评判和分析
        """
        try:
            # 使用form-data格式接收数据
            prompt = request.form.get('prompt', None)
            question = request.form.get('question', None)
            user_id = getattr(g, 'current_user_id', None)
            question_uid = request.form.get('question_uid', None)
            race_id = int(request.form.get('race_id', 0))

            if user_id is None:
                return {
                    "success": False,
                    "message": "用户未登录"
                }, 401

            if not all([prompt, question, question_uid]):
                return {
                    "success": False,
                    "message": "字段不能为空"
                }, 400

            result = generate_completion(explain2 + judge_prompt + question_start + question + question_end + prompt,
                                         model="deepseek-r1:7b")
            return judge_question(user_id, question_uid, race_id, result)

        except Exception as e:
            return {
                "success": False,
                "message": str(e)
            }, 500
