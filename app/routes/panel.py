import time

from flask import g
from flask_restx import Resource

from app import api, redis_wrapper
from app.services.panel_service import get_stats
from app.utils.role_utils import optional_login

panel_ns = api.namespace('Panel', description='面板相关接口', path='/api')


@panel_ns.route('/getStats')
class GetStats(Resource):
    def get(self):
        """获取注册人数，题目数，竞赛数"""
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
