from flask_restx import Resource, fields
from app import api, db
from app.utils.role_utils import role_required
from app.models import QuestionsData

# 创建命名空间
admin_questions_ns = api.namespace('Admin-Questions', description='题目管理接口', path='/api')

# 题目难度枚举
TOPIC_ENUM = ['入门', '普及', '提高', '省选', 'NOI', 'CTSC']

# 示例模型
example_model = admin_questions_ns.model('Example', {
    'input': fields.String,
    'output': fields.String,
    'explanation': fields.String
})

# 创建题目输入模型（严格验证）
create_question_model = admin_questions_ns.model('CreateQuestion', {
    'uid': fields.Integer(required=True, example=1),
    'question': fields.Nested(admin_questions_ns.model('QuestionData', {
        'title': fields.String(required=True, min_length=1, example='两数之和'),
        'description': fields.String(required=True, min_length=1, example='计算两个整数的和'),
        'time_limit': fields.Integer(required=True, min=100, example=1000),
        'memory_limit': fields.Integer(required=True, min=1, example=128),
        'input_format': fields.String(example='两个整数，空格分隔'),
        'output_format': fields.String(example='一个整数'),
        'constraints': fields.List(fields.String, example=['-1000 ≤ a, b ≤ 1000']),
        'examples': fields.List(fields.Nested(example_model))
    })),
    'topic': fields.String(required=True, enum=TOPIC_ENUM, example='入门')
})

# 更新题目模型（所有字段可选）
update_question_model = admin_questions_ns.model('UpdateQuestion', {
    'question': fields.Nested(admin_questions_ns.model('QuestionUpdateData', {
        'title': fields.String(min_length=1),
        'description': fields.String(min_length=1),
        'time_limit': fields.Integer(min=100),
        'memory_limit': fields.Integer(min=1),
        'input_format': fields.String,
        'output_format': fields.String,
        'constraints': fields.List(fields.String),
        'examples': fields.List(fields.Nested(example_model))
    })),
    'topic': fields.String(enum=TOPIC_ENUM)
})


@admin_questions_ns.route('/admin-question')
class AdminQuestionList(Resource):
    @admin_questions_ns.marshal_list_with(create_question_model)
    @role_required('admin')
    def get(self):
        """获取所有题目列表（管理员）"""
        return QuestionsData.query.all()

    @admin_questions_ns.expect(create_question_model)
    @admin_questions_ns.response(400, '参数验证失败')
    @admin_questions_ns.response(201, '创建成功')
    @role_required('admin')
    def post(self):
        """创建新题目（严格验证）"""
        data = api.payload

        # 手动验证必填字段
        if not all(key in data['question'] for key in ['title', 'description', 'time_limit', 'memory_limit']):
            return {
                "success": False,
                "message": "缺少必填字段: title, description, time_limit, memory_limit"
            }

        # 验证难度类型
        if data['topic'] not in TOPIC_ENUM:
            return {
                "success": False,
                "message": f'难度必须是以下之一: {", ".join(TOPIC_ENUM)}'
            }

        new_question = QuestionsData(
            question={
                'title': data['question']['title'],
                'description': data['question']['description'],
                'time_limit': data['question']['time_limit'],
                'memory_limit': data['question']['memory_limit'],
                'input_format': data['question'].get('input_format', ''),
                'output_format': data['question'].get('output_format', ''),
                'constraints': data['question'].get('constraints', []),
                'examples': data['question'].get('examples', [])
            },
            topic=data['topic']
        )

        db.session.add(new_question)
        db.session.commit()
        return {'success': True, 'message': f'新增题目成功，uid：{new_question.uid}'}, 201


@admin_questions_ns.route('/<int:question_id>')
class AdminQuestionDetail(Resource):
    @admin_questions_ns.response(404, '题目不存在')
    @role_required('admin')
    def delete(self, question_id):
        """删除题目"""
        question = QuestionsData.query.get(question_id)
        if not question:
            return {'success': False, 'message': '题目不存在'}, 404

        db.session.delete(question)
        db.session.commit()
        return {'success': True, 'message': '删除成功'}, 200

    @admin_questions_ns.expect(update_question_model)
    @admin_questions_ns.response(400, '参数验证失败')
    @admin_questions_ns.response(404, '题目不存在')
    @role_required('admin')
    def put(self, question_id):
        """更新题目信息"""
        question = QuestionsData.query.get(question_id)
        if not question:
            return {'success': False, 'message': '题目不存在'}, 404

        data = api.payload
        update_data = {}

        # 只更新提供的字段
        if 'question' in data:
            current = question.question
            update_data['question'] = {
                'title': data['question'].get('title', current['title']),
                'description': data['question'].get('description', current['description']),
                'time_limit': data['question'].get('time_limit', current['time_limit']),
                'memory_limit': data['question'].get('memory_limit', current['memory_limit']),
                'input_format': data['question'].get('input_format', current.get('input_format', '')),
                'output_format': data['question'].get('output_format', current.get('output_format', '')),
                'constraints': data['question'].get('constraints', current.get('constraints', [])),
                'examples': data['question'].get('examples', current.get('examples', []))
            }

        if 'topic' in data:
            if data['topic'] not in TOPIC_ENUM:
                return {
                    "success": False,
                    "message": f'难度必须是以下之一: {", ".join(TOPIC_ENUM)}'
                }
            update_data['topic'] = data['topic']

        # 执行更新
        for key, value in update_data.items():
            setattr(question, key, value)

        db.session.commit()
        return {'success': True, 'message': '更新成功'}, 200

    @admin_questions_ns.marshal_with(create_question_model)
    @admin_questions_ns.response(404, '题目不存在')
    @role_required('admin')
    def get(self, question_id):
        """获取题目详情"""
        question = QuestionsData.query.get_or_404(question_id)
        return question
