from flask import request
from flask_restx import Resource, Model, fields, Namespace
from app.services.user_info_service import get_user_list_service, ban_user, unban_user, update_user_role_service
from app.utils.role_utils import role_required

admin_userManage = Namespace('Admin-UserManage', description='管理员用户管理相关接口', path='/api')

# 定义POST请求的请求体模型
user_list_params = admin_userManage.model("UserListParams", {
    "uid": fields.Integer(description="用户ID（可选）", required=False),
    "username": fields.String(description="用户名（模糊搜索）", required=False),
    "rating": fields.Integer(description="用户评级（可选）", required=False),
    "page": fields.Integer(description="分页页码（默认1）", default=1, required=False)
})


@admin_userManage.route('/admin-get-user-list')
class AdminGetUserList(Resource):
    @admin_userManage.doc(
        security='Bearer',
        description='获取用户列表（POST方式）'
    )
    @admin_userManage.expect(user_list_params)  # 使用expect指定请求体模型
    @role_required('admin', 'superAdmin')
    def post(self):
        """通过POST请求获取用户列表（支持分页和过滤）"""
        try:
            # 从请求体中获取JSON参数
            data = request.get_json()
            uid = data.get('uid')
            username = data.get('username', '')
            rating = data.get('rating')
            page = data.get('page', 1)

            # 调用服务层函数
            return get_user_list_service(uid, username, rating, page)

        except Exception as e:
            return {
                "success": False,
                "message": f"获取用户列表失败: {str(e)}"
            }, 500


@admin_userManage.route('/admin-ban-user')
class AdminBanUser(Resource):
    @admin_userManage.doc(
        security='Bearer',
        description='封禁用户（POST方式）'
    )
    @admin_userManage.expect(admin_userManage.model("BanUserParams", {
        "uid": fields.Integer(description="用户ID", required=True),
        "ban_reason": fields.String(description="封禁原因", required=True),
        "ban_end_time": fields.DateTime(description="封禁结束时间（可选）", required=False, example='2077-7-7 11:45:14')
    }))
    @role_required('admin', 'superAdmin')
    def post(self):
        """通过POST请求封禁用户"""
        try:
            data = request.get_json()
            uid = data['uid']
            ban_reason = data['ban_reason']
            ban_end_time = data.get('ban_end_time')

            # 调用服务层函数进行封禁操作
            return ban_user(uid, ban_reason, ban_end_time)

        except Exception as e:
            return {
                "success": False,
                "message": f"封禁用户失败: {str(e)}"
            }, 500


@admin_userManage.route('/admin-unban-user')
class AdminUnbanUser(Resource):
    @admin_userManage.doc(
        security='Bearer',
        description='解封用户（POST方式）'
    )
    @admin_userManage.expect(admin_userManage.model("UnbanUserParams", {
        "uid": fields.Integer(description="用户ID", required=True)
    }))
    @role_required('admin', 'superAdmin')
    def post(self):
        """通过POST请求解封用户"""
        try:
            data = request.get_json()
            uid = data['uid']

            # 调用服务层函数进行解封操作
            return unban_user(uid)  # 解封时传入None表示解除封禁

        except Exception as e:
            return {
                "success": False,
                "message": f"解封用户失败: {str(e)}"
            }, 500


@admin_userManage.route('/update-user-role')
class UpdateUserRole(Resource):
    @admin_userManage.doc(
        security='Bearer',
        description='更新用户角色（POST方式）'
    )
    @admin_userManage.expect(admin_userManage.model("UpdateUserRoleParams", {
        "uid": fields.Integer(description="用户ID", required=True),
        "new_role": fields.String(description="新角色（user, admin）", required=True)
    }))
    @role_required('superAdmin')
    def post(self):
        """通过POST请求更新用户角色"""
        try:
            data = request.get_json()
            uid = data['uid']
            new_role = data['new_role']

            # 调用服务层函数进行角色更新
            return update_user_role_service(uid, new_role)

        except Exception as e:
            return {
                "success": False,
                "message": f"更新用户角色失败: {str(e)}"
            }, 500
