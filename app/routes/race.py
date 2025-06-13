from flask_restx import Resource, fields
from flask import request, g
from app import api, db
from app.services.race_service import get_race_info, get_race_list, get_race_rank, register_race, get_start_race_list
from app.utils.race_task import race_reminder_task, check_race_status
from app.utils.role_utils import optional_login
from app.utils.validators import BusinessException

# 创建比赛信息命名空间
race_ns = api.namespace('Race', description='比赛信息接口', path='/api')

# 请求模型定义
race_info_model = race_ns.model('RaceInfo', {
    'uid': fields.Integer(required=True, description='比赛ID', example=1)
})

race_rank_model = race_ns.model('RaceRank', {
    'uid': fields.String(required=True, description='比赛UID')
})

race_register_model = race_ns.model('RaceRegister', {
    'race_uid': fields.Integer(required=True, description='比赛ID', example=1)
})


@race_ns.route('/race-info')
class RaceInfo(Resource):
    @race_ns.doc(security='Bearer', description='获取比赛详细信息')
    @race_ns.expect(race_info_model)
    @optional_login
    def post(self):
        """获取比赛详细信息"""
        try:
            data = request.get_json()
            user_id = getattr(g, 'current_user_id', None)
            return get_race_info(
                race_id=int(data.get('uid', 1)),
                user_id=user_id
            )
        except ValueError:
            return {
                "success": False,
                "message": "参数类型错误"
            }, 400


@race_ns.route('/race-list')
class RaceList(Resource):
    @race_ns.doc(description='获取比赛列表')
    def get(self):
        """获取所有比赛列表"""
        return get_race_list()


@race_ns.route('/race-rank')
class RaceRank(Resource):
    @race_ns.doc(description='获取比赛排名')
    @race_ns.expect(race_rank_model)
    def post(self):
        """获取指定比赛的排名"""
        data = request.get_json()
        if not data:
            return {
                "success": False,
                "message": "请求数据必须是JSON格式"
            }, 400

        race_uid = data.get('uid', '')
        return get_race_rank(race_uid)


# 添加报名接口
@race_ns.route('/race-register')
class RaceRegister(Resource):
    @race_ns.doc(security='Bearer', description='比赛报名接口')
    @race_ns.expect(race_register_model)
    @optional_login
    def post(self):
        """比赛报名"""
        try:
            # 1. 获取当前用户ID
            user_id = getattr(g, 'current_user_id', None)
            if not user_id:
                return {"success": False, "message": "请先登录"}, 401

            # 2. 获取请求数据
            data = request.get_json()
            race_uid = data.get('race_uid')

            if not race_uid:
                return {"success": False, "message": "比赛ID不能为空"}, 400

            # 3. 调用服务层
            return register_race(user_id, race_uid)

        except BusinessException as e:
            return {"success": False, "message": e.message}, e.status_code
        except Exception as e:
            db.session.rollback()
            return {"success": False, "message": f"报名过程中发生错误: {str(e)}"}, 500


@race_ns.route('/test-send-race-email')
class GetTmpRace(Resource):
    def get(self):
        """发送比赛提醒邮件（测试用）"""
        result = race_reminder_task.delay()
        # result = check_race_status.delay()
        return result.get()
