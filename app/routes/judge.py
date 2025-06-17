from flask import g
from flask_restx import Resource, reqparse
import os

from datetime import datetime as dt

import config
from app import api
from app.models import QuestionsData
from app.services.judge_service import _judge_cpp
from app.services.panel_service import update_user_heatmap
from app.services.question_service import add_question_record, update_user_question_status
from app.services.race_service import validate_race_access, update_race_rank
from app.utils.role_utils import optional_login
from app.utils.validators import safe_int

judge_ns = api.namespace('judge', description='判题相关', path='/api/judge')

# 请求参数解析器 - 使用 form-data
judge_parser = reqparse.RequestParser()
judge_parser.add_argument('code', type=str, required=True, help='用户提交的代码', location='form')
judge_parser.add_argument('language', type=str, required=True, choices=['cpp', 'c'],
                          help='编程语言', location='form')
judge_parser.add_argument('problem_id', type=int, required=True, help='问题ID', location='form')
judge_parser.add_argument('race_id', type=int, required=False, help='比赛ID（可选）', location='form')


@judge_ns.route('/submit')
class JudgeSubmission(Resource):
    @judge_ns.expect(judge_parser)
    @optional_login
    def post(self):
        """提交代码进行判题"""
        args = judge_parser.parse_args()
        code = args['code']
        language = args['language']
        problem_id = args['problem_id']
        race_id = safe_int(args.get('race_id', 0))
        user_id = getattr(g, 'current_user_id', None)

        if not user_id:
            return {"success": False, "message": "请先登录"}, 401

        if not all([code, language, problem_id]):
            return {"success": False, "message": "缺少必要参数"}, 400

        if race_id > 0:
            is_valid, err_msg, err_code = validate_race_access(user_id, race_id)
            if not is_valid:
                return {"success": False, "message": err_msg}, err_code

        question = QuestionsData.query.filter_by(uid=problem_id).first()
        time_limit = question.question.get('time_limit')
        memory_limit = question.question.get('memory_limit') * 1024 * 1024

        # 1. 准备测试用例
        test_cases_dir = config.Config.TESTCASE_DIR + f"/testcases_{problem_id}"
        if not os.path.exists(test_cases_dir):
            return {"success": False, "message": "测试用例不存在"}, 404

        # 2. 根据语言编译/准备代码
        try:
            if language == 'cpp':
                result = _judge_cpp(code, test_cases_dir, time_limit, memory_limit)

                is_passed = False
                if result['status'] == 'Accepted':
                    is_passed = True
                    update_user_heatmap(user_id, dt.now().strftime("%Y-%m-%d"))

                add_question_record(user_id, problem_id, is_passed)
                update_user_question_status(user_id, problem_id, is_passed, race_id=race_id)
                if race_id and race_id > 0:
                    update_race_rank(user_id, problem_id, is_passed, race_id)

            else:
                return {"success": False, "message": "不支持的语言"}, 400
        except Exception as e:
            return {"success": False, "message": f"判题过程中出错: {str(e)}"}, 500

        return {"success": True, "result": result}
