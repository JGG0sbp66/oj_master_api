from flask_restx import Resource

from app import api
from app.services.panel_service import get_stats

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
