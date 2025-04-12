from flask_restx import Resource
from app import api  # 从主模块导入api实例
from app.utils.role_utils import role_required

# 创建命名空间
admin_ns = api.namespace('Admin', description='管理员接口', path='/api')


@admin_ns.route('/admin-dashboard')
class AdminDashboard(Resource):
    @admin_ns.doc(security='Bearer')  # 声明需要认证
    @role_required('admin')
    def get(self):
        """管理员仪表盘 (GET请求)"""
        return {
            'success': True,
            'message': 'IM ADMIN'
        }

    @admin_ns.doc(security='Bearer')
    @role_required('admin')
    def post(self):
        """管理员仪表盘 (POST请求)"""
        return {
            'success': True,
            'message': 'POST操作成功'
        }
