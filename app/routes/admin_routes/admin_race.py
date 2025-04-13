from flask_restx import Resource, fields
from datetime import datetime
from app import api, db
from app.models import RaceData
from app.utils.role_utils import role_required

# 创建命名空间
admin_ns = api.namespace('Admin-Race', description='比赛管理接口', path='/api')

# 定义数据模型

# 子模型
tag_model = admin_ns.model('RaceTag', {
    'name': fields.String(required=True, example='未开始'),
    'type': fields.String(required=True, example='pending')
})

# 主响应模型
race_model = admin_ns.model('Race', {
    'uid': fields.Integer(readOnly=True, description='比赛唯一ID'),
    'title': fields.String(required=True, description='比赛名称'),
    'logos': fields.List(
        fields.String,
        example=["ACM", "ICPC"],
        description='主办方logo数组'
    ),
    'start_time': fields.DateTime(required=True, description='开始时间'),
    'end_time': fields.DateTime(required=True, description='结束时间'),
    'duration': fields.String(description='持续时间，如"04小时00分00秒"'),
    'tags': fields.List(
        fields.Nested(tag_model),
        example=[{"name": "未开始", "type": "pending"}],
        description='标签数组'
    ),
    'created_at': fields.DateTime(readOnly=True, description='创建时间'),
    'updated_at': fields.DateTime(readOnly=True, description='更新时间'),
    'problems_list': fields.List(
        fields.Integer,
        example=[1, 2, 3],
        description='题目UID数组'
    ),
    'user_list': fields.List(
        fields.Integer,
        example=[101, 102, 103],
        description='报名用户UID数组'
    ),
    'status': fields.String(description='比赛状态')
})

# 创建比赛输入模型
create_race_input_model = admin_ns.model('RaceInput', {
    'title': fields.String(required=True, description='比赛名称'),
    'logos': fields.List(
        fields.String,
        required=True,
        example=["ACM", "ICPC"],
        description='主办方logo数组'
    ),
    'start_time': fields.String(required=True, description='开始时间(ISO格式)'),
    'end_time': fields.String(required=True, description='结束时间(ISO格式)'),
    'tags': fields.List(
        fields.Nested(tag_model),
        required=True,
        example=[{"name": "未开始", "type": "pending"}],
        description='标签数组'
    ),
    'problems_list': fields.List(
        fields.Integer,
        required=True,
        example=[1, 2, 3],
        description='题目UID数组'
    )
})

# 更新比赛输入模型
update_race_input_model = admin_ns.model('RaceUpdate', {
    'title': fields.String(required=False, description='比赛名称'),
    'logos': fields.List(
        fields.String,
        required=False,
        example=["ACM", "ICPC"],
        description='主办方logo数组'
    ),
    'start_time': fields.String(required=False, description='开始时间(ISO格式)'),
    'end_time': fields.String(required=False, description='结束时间(ISO格式)'),
    'tags': fields.List(
        fields.Nested(tag_model),
        required=False,
        example=[{"name": "未开始", "type": "pending"}],
        description='标签数组'
    ),
    'problems_list': fields.List(
        fields.Integer,
        required=False,
        example=[1, 2, 3],
        description='题目UID数组'
    ),
    'user_list': fields.List(
        fields.Integer,
        required=False,
        example=[101, 102, 103],
        description='报名用户UID数组'
    )
})


@admin_ns.route('/races')
class RaceList(Resource):
    @admin_ns.doc(security='Bearer')
    @role_required('admin')
    @admin_ns.marshal_list_with(race_model)
    def get(self):
        """获取所有比赛列表"""
        races = RaceData.query.all()
        return races

    @admin_ns.doc(security='Bearer')
    @role_required('admin')
    @admin_ns.expect(create_race_input_model)
    def post(self):
        """创建新比赛"""
        data = api.payload

        # 转换时间格式
        try:
            start_time = datetime.fromisoformat(data['start_time'])
            end_time = datetime.fromisoformat(data['end_time'])
        except ValueError:
            return {"success": False, "message": "时间格式错误，请使用ISO格式(如: 2023-01-01T00:00:00)"}, 400

        # 检查时间有效性
        if end_time <= start_time:
            return {"success": False, "message": "结束时间必须晚于开始时间"}, 400

        # 计算持续时间
        duration_seconds = (end_time - start_time).total_seconds()
        hours = int(duration_seconds // 3600)
        minutes = int((duration_seconds % 3600) // 60)
        seconds = int(duration_seconds % 60)
        duration = f"{hours:02d}小时{minutes:02d}分{seconds:02d}秒"

        # 设置默认状态
        now = datetime.now()
        status = 'upcoming' if start_time > now else 'running' if start_time <= now <= end_time else 'ended'

        new_race = RaceData(
            title=data['title'],
            logos=data['logos'],
            start_time=start_time,
            end_time=end_time,
            duration=duration,
            tags=data['tags'],
            problems_list=data['problems_list'],
            user_list=[],
            status=status
        )

        db.session.add(new_race)
        db.session.commit()

        return {"success": True, "message": "新增比赛成功"}, 201


@admin_ns.route('/races/<int:race_id>')
class RaceDetail(Resource):
    @admin_ns.doc(security='Bearer')
    @role_required('admin')
    @admin_ns.marshal_with(race_model)
    def get(self, race_id):
        """获取单个比赛详情"""
        race = RaceData.query.get_or_404(race_id)
        return race

    @admin_ns.doc(security='Bearer')
    @role_required('admin')
    @admin_ns.expect(update_race_input_model)
    def put(self, race_id):
        """更新比赛信息"""
        race = RaceData.query.get(race_id)
        data = api.payload

        if not RaceData:
            return {"success": False, "message": "更新失败，比赛不存在"}, 404

        # 更新字段
        if 'title' in data:
            race.title = data['title']
        if 'logos' in data:
            race.logos = data['logos']
        if 'tags' in data:
            race.tags = data['tags']
        if 'problems_list' in data:
            race.problems_list = data['problems_list']
        if 'user_list' in data:
            race.user_list = data['user_list']

        # 处理时间更新
        if 'start_time' in data or 'end_time' in data:
            start_time = datetime.fromisoformat(data['start_time']) if 'start_time' in data else race.start_time
            end_time = datetime.fromisoformat(data['end_time']) if 'end_time' in data else race.end_time

            if end_time <= start_time:
                return {"message": "结束时间必须晚于开始时间"}, 400

            race.start_time = start_time
            race.end_time = end_time
            duration_seconds = (end_time - start_time).total_seconds()
            hours = int(duration_seconds // 3600)
            minutes = int((duration_seconds % 3600) // 60)
            seconds = int(duration_seconds % 60)
            race.duration = f"{hours:02d}小时{minutes:02d}分{seconds:02d}秒"

        db.session.commit()
        return {"success": True, "message": "修改比赛成功"}, 201

    @admin_ns.doc(security='Bearer')
    @role_required('admin')
    def delete(self, race_id):
        """删除比赛"""
        try:
            race = RaceData.query.get(race_id)
            if not race:
                return {
                    "success": False,
                    "message": "删除比赛失败，比赛不存在"
                }, 404
            db.session.delete(race)
            db.session.commit()
            return {
                "success": True,
                'message': '删除比赛成功'
            }, 200
        except Exception as e:
            db.session.rollback()  # 发生错误时回滚
            return {
                "success": False,
                "message": f"删除比赛失败: {str(e)}"
            }, 500
