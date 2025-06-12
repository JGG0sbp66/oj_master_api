import time
from datetime import datetime

from flask import g
from flask_restx import Resource, fields

from app import api, redis_wrapper
from app.services.panel_service import get_stats, get_user_heatmap
from app.utils.role_utils import optional_login

panel_ns = api.namespace('Panel', description='面板相关接口', path='/api')


@panel_ns.route('/getStats')
class GetStats(Resource):
    def get(self):
        """获取注册人数，题目数，竞赛数，在线用户数"""
        try:
            return get_stats()
        except Exception as e:
            return {
                "success": False,
                "message": f"获取统计信息失败: {str(e)}"
            }, 500


@panel_ns.route('/heartbeat')
class Heartbeat(Resource):
    @optional_login
    def post(self):
        """心跳检测，判断用户是否在线"""
        try:
            user_id = getattr(g, 'current_user_id', None)

            if user_id is None:
                return {
                    "success": False,
                    "message": "当前用户为游客"
                }, 401

            redis_wrapper.setex(f"online:{user_id}", 65, int(time.time()))

            return {
                "success": True,
                "user_id": user_id,
                "status": "保持连接",
            }

        except Exception as e:
            return {
                "success": False,
                "message": f"心跳检测失败: {str(e)}"
            }


date_range_parser = api.parser()
date_range_parser.add_argument('year', type=int, help='年份', default=datetime.now().year)

heatmap_model = api.model('HeatmapData', {
    'date': fields.String(description='日期'),
    'score': fields.Integer(description='用户通过数量')
})

response_model = api.model('HeatmapResponse', {
    'year': fields.Integer,
    'user_id': fields.Integer,
    'data': fields.List(fields.Nested(heatmap_model)),
})


@panel_ns.route('/getHeatmap')
class GetHeatmap(Resource):
    @panel_ns.expect(date_range_parser)
    @panel_ns.marshal_with(response_model)
    @optional_login
    def get(self):
        """获取用户热力图数据"""
        args = date_range_parser.parse_args()
        year = args.get('year', datetime.now().year)
        user_id = getattr(g, 'current_user_id', None)

        result = get_user_heatmap(user_id, year)

        return {
            "year": year,
            "user_id": user_id,
            "data": [
                {
                    "date": item.activity_date.strftime('%Y-%m-%d'),
                    "score": item.activity_score
                } for item in result
            ]
        }