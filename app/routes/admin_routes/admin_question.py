import os
import shutil

from flask import current_app, request
from werkzeug.datastructures import FileStorage
from flask_restx import Resource, fields, reqparse
from app import api, db
from app.services.question_service import admin_get_questions
from app.services.testcase_service import process_test_cases, move_test_cases
from app.utils.file_utils import save_uploaded_file, extract_zip_file
from app.utils.role_utils import role_required
from app.models import QuestionsData, UserQuestionStatus
from config import Config

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
    'topic': fields.String(required=True, enum=TOPIC_ENUM, example='入门'),
    'submit_num': fields.Integer(example=0, description='总提交次数'),
    'solve_num': fields.Integer(example=0, description='总解决次数'),
    'updated_at': fields.String(description='最后更新时间', example='2023-10-01'),
    'is_contest_question': fields.Integer(default=0, description='是否为比赛题目，0表示否，1表示是')
})

question_list_model = admin_questions_ns.model('QuestionList', {
    'page': fields.Integer(description='页码', default=1),
    'topic': fields.String(description='难度', default=''),
    'input': fields.String(description='题目名', default='')
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

# 上传测试用例模型
testcase_upload_model = admin_questions_ns.model('TestcaseUpload', {
    'problem_id': fields.Integer(required=True, description='题目ID'),
    'testcase_file': fields.String(required=True, description='测试用例ZIP文件', example='testcases.zip')
})


@admin_questions_ns.route('/admin-get-questions')
class AdminGetQuestions(Resource):
    @admin_questions_ns.expect(question_list_model)
    @role_required('admin', 'superAdmin')
    def post(self):
        """按照条件筛选"""
        try:
            data = request.get_json()

            result = admin_get_questions(
                page=int(data.get('page', 1)),
                topic=str(data.get('topic', '')).strip(),
                textinput=str(data.get('input', '')).strip()
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


@admin_questions_ns.route('/admin-question')
class AdminQuestionList(Resource):
    @admin_questions_ns.marshal_list_with(create_question_model)
    @role_required('admin', 'superAdmin')
    def get(self):
        """获取所有题目列表（管理员）"""
        # 获取所有题目
        questions = QuestionsData.query.all()
        question_ids = [q.uid for q in questions]

        # 批量获取统计信息（race_id=0, user_id=0）
        stats_query = UserQuestionStatus.query.filter(
            UserQuestionStatus.race_id == 0,
            UserQuestionStatus.user_id == 0,
            UserQuestionStatus.question_id.in_(question_ids)
        ).all()

        stats_dict = {s.question_id: {
            "submit_num": s.submit or 0,
            "solve_num": s.solve or 0
        } for s in stats_query}

        # 构建响应数据
        result = []
        for q in questions:
            stats = stats_dict.get(q.uid, {
                "submit_num": 0,
                "solve_num": 0
            })
            submit_num = stats["submit_num"]
            solve_num = stats["solve_num"]

            question_data = {
                "uid": q.uid,
                "question": q.question,
                "topic": q.topic,
                "submit_num": submit_num,
                "solve_num": solve_num,
                "updated_at": q.updated_at.strftime('%Y-%m-%d'),
            }
            result.append(question_data)

        return result

    @admin_questions_ns.expect(create_question_model)
    @admin_questions_ns.response(400, '参数验证失败')
    @admin_questions_ns.response(201, '创建成功')
    @role_required('admin', 'superAdmin')
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
            topic=data['topic'],
            is_contest_question=data.get('is_contest_question', 0),
        )

        db.session.add(new_question)
        db.session.commit()
        return {
            'success': True,
            'message': '新增题目成功',
            'uid': new_question.uid
        }, 201


@admin_questions_ns.route('/admin-question/<int:question_id>')
class AdminQuestionDetail(Resource):
    @admin_questions_ns.response(404, '题目不存在')
    @role_required('admin', 'superAdmin')
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
    @role_required('admin', 'superAdmin')
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
    @role_required('admin', 'superAdmin')
    def get(self, question_id):
        """获取题目详情"""
        question = QuestionsData.query.get_or_404(question_id)
        return question


# 创建文件上传的解析器
file_upload_parser = reqparse.RequestParser()
file_upload_parser.add_argument(
    'file',
    type=FileStorage,
    location='files',
    required=True,
    help='包含测试用例的ZIP文件'
)


@admin_questions_ns.route('/testcase-upload/<int:question_id>')
class TestCaseUploadQuestion(Resource):
    @admin_questions_ns.expect(testcase_upload_model)
    @admin_questions_ns.response(400, '参数验证失败')
    @role_required('admin', 'superAdmin')
    def post(self, question_id):
        """上传测试用例"""
        try:
            args = file_upload_parser.parse_args()
            uploaded_file = args['file']

            # 验证文件扩展名
            if not ('.' in uploaded_file.filename and
                    uploaded_file.filename.rsplit('.', 1)[1].lower() in Config.ALLOWED_TESTCASE_EXTENSIONS):
                return {
                    "success": False,
                    "message": "文件格式有误，请上传zip格式压缩包"
                }, 400

            # 创建必要的目录
            os.makedirs(Config.TESTCASE_UPLOAD_DIR + '/zip', exist_ok=True)
            os.makedirs(Config.TESTCASE_UPLOAD_DIR + '/extracted', exist_ok=True)
            os.makedirs(os.path.join(Config.TESTCASE_UPLOAD_DIR, '../problems'), exist_ok=True)

            # 保存上传的文件
            zip_path = save_uploaded_file(uploaded_file,
                                          os.path.join(Config.TESTCASE_UPLOAD_DIR, 'zip'),
                                          f"testcases_{question_id}")

            # 解压ZIP文件
            extract_dir = os.path.join(Config.TESTCASE_UPLOAD_DIR, 'extracted', f"testcases_{question_id}")
            extracted_files = extract_zip_file(zip_path, extract_dir)

            # 处理测试用例
            result = process_test_cases(extract_dir)

            if len(result.get('errors', [])) == 0:
                # 正确的目标路径
                target_dir = os.path.join(Config.TESTCASE_UPLOAD_DIR, '../problems', f"testcases_{question_id}")
                move_test_cases(extract_dir, target_dir)

                # 清理临时文件
                shutil.rmtree(extract_dir)
                os.remove(zip_path)
            else:
                return {
                    "success": False,
                    "message": "测试用例处理失败",
                    "details": result['errors']
                }, 400

            return {
                "success": True,
                "message": "测试用例已成功上传并处理",
                "details": {
                    "question_id": question_id,
                    "test_cases_count": result['count'],
                    "processed_files": extracted_files
                }
            }

        except Exception as e:
            current_app.logger.error(f"测试用例上传失败: {str(e)}", exc_info=True)
            return {
                "success": False,
                "message": "测试用例上传处理失败",
                "error": str(e)
            }, 500
