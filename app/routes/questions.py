from flask_restx import Resource, fields
from flask import request, g
from app import api
from app.services.question_service import get_questions, get_question_detail, get_recent_questions
from app.utils.role_utils import optional_login

# 创建问题相关接口命名空间
questions_ns = api.namespace('Questions', description='问题相关接口', path='/api')

# 模型定义
question_list_model = questions_ns.model('QuestionList', {
    'page': fields.Integer(description='页码', default=1),
    'category': fields.String(description='分类', default=''),
    'topic': fields.String(description='难度', default=''),
    'input': fields.String(description='题目名', default='')
})

question_detail_model = questions_ns.model('QuestionDetail', {
    'uid': fields.Integer(required=True, description='问题ID')
})


@questions_ns.route('/questions')
class QuestionList(Resource):
    @questions_ns.doc(security='Bearer', description='获取问题列表')
    @questions_ns.expect(question_list_model)
    @optional_login
    def post(self):
        """获取问题列表"""
        try:
            data = request.get_json()
            user_id = getattr(g, 'current_user_id', None)  # 获取当前用户ID

            result = get_questions(
                page=int(data.get('page', 1)),
                category=str(data.get('category', '')).strip(),
                topic=str(data.get('topic', '')).strip(),
                textinput=str(data.get('input', '')).strip(),
                user_id=user_id
            )

            return {
                "success": True,
                "questions": result.get('questions', []),
                "total_page": result.get('total_page', 1),
                "total_count": result.get('total_count', 0)
            }
        except ValueError:
            return {
                "success": False,
                "message": "参数类型错误"
            }, 400


@questions_ns.route('/question-detail')
class QuestionDetail(Resource):
    @questions_ns.doc(description='获取问题详情')
    @questions_ns.expect(question_detail_model)
    def post(self):
        """获取问题详情"""
        try:
            data = request.get_json()
            if not data:
                return {
                    "success": False,
                    "message": "请求数据必须是JSON格式"
                }, 400

            question_id = data.get('uid', '')
            result = get_question_detail(int(question_id))
            return {
                "success": True,
                "question_detail": result
            }
        except ValueError:
            return {
                "success": False,
                "message": "参数类型错误"
            }, 400


@questions_ns.route('/home-get-question')
class HomeGetQuestion(Resource):
    @questions_ns.doc(description='获取首页问题')
    def get(self):
        """获取首页问题（按更新时间倒序）"""
        try:
            questions = get_recent_questions()

            return {
                "success": True,
                "questions": questions
            }
        except ValueError:
            return {
                "success": False,
                "message": "参数类型错误"
            }, 400
