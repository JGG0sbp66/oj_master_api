from flask_restx import Resource, fields
from flask import request, g
from app import api  # 从主模块导入api实例
from app.services.user_info_service import to_chance_password, to_change_username, to_change_email, get_user_info, \
    get_username
from app.services.user_info_service import get_avatar_service, save_avatar, get_user_questions, get_user_race
from app.utils.role_utils import optional_login, role_required

# 创建用户信息命名空间
user_info_ns = api.namespace('User', description='用户信息相关接口', path='/api')

# 模型定义
avatar_upload_model = api.model('AvatarUpload', {
    'file': fields.Raw(description='头像文件', required=True)
})

password_change_model = api.model('PasswordChange', {
    'old_password': fields.String(required=True, description='旧密码'),
    'new_password': fields.String(required=True, description='新密码'),
    're_new_password': fields.String(required=True, description='确认新密码')
})

username_change_model = api.model('UsernameChange', {
    'new_username': fields.String(required=True, description='新用户名')
})

email_change_model = api.model('EmailChange', {
    'new_email': fields.String(required=True, description='新邮箱'),
    'new_email_code': fields.String(required=True, description='新邮箱验证码')
})


# 用户信息接口
@user_info_ns.route('/avatar-get/<int:user_id>')
class AvatarGet(Resource):
    @user_info_ns.doc(description='获取用户头像')
    def get(self, user_id):
        """获取用户头像"""
        try:
            return get_avatar_service(user_id)
        except Exception as e:
            return {
                "success": False,
                "message": f"获取头像失败: {str(e)}"
            }, 500


@user_info_ns.route('/avatar-upload')
class AvatarUpload(Resource):
    @user_info_ns.doc(security='Bearer', description='上传用户头像')
    @user_info_ns.expect(avatar_upload_model)
    @optional_login
    def post(self):
        """上传用户头像"""
        try:
            user_id = getattr(g, 'current_user_id', None)
            if user_id is None:
                return {
                    "success": False,
                    "message": "无效的用户"
                }, 401

            # 检查是否有文件在请求中
            if 'file' not in request.files:
                return {
                    "success": False,
                    "message": "没有文件部分"
                }, 400

            file = request.files['file']

            # 调用函数保存头像
            filename = save_avatar(user_id, file)

            return {
                "success": True,
                "message": "头像更新成功",
                "filename": filename
            }, 200

        except Exception as e:
            return {
                "success": False,
                "message": f"更新头像失败: {str(e)}"
            }, 500


@user_info_ns.route('/get-user-info')
class GetUserInfo(Resource):
    @optional_login
    def get(self):
        """获取用户信息"""
        try:
            user_id = getattr(g, 'current_user_id', None)
            if user_id is None:
                return {
                    "success": False,
                    "message": "无效的用户"
                }, 401

            return get_user_info(user_id)
        except Exception as e:
            return {
                "success": False,
                "message": f"获取用户信息失败: {str(e)}"
            }, 500


@user_info_ns.route('/user-questions')
class UserQuestions(Resource):
    @user_info_ns.doc(security='Bearer', description='获取用户题目')
    @optional_login
    def get(self):
        """获取用户题目"""
        try:
            user_id = getattr(g, 'current_user_id', None)
            if user_id is None:
                return {
                    "success": False,
                    "message": "无效的用户"
                }, 401

            return get_user_questions(user_id)
        except Exception as e:
            return {
                "success": False,
                "message": f"获取用户题目失败: {str(e)}"
            }, 500


@user_info_ns.route('/user-race')
class UserRace(Resource):
    @user_info_ns.doc(security='Bearer', description='获取用户比赛')
    @optional_login
    def get(self):
        """获取用户比赛"""
        try:
            user_id = getattr(g, 'current_user_id', None)
            if user_id is None:
                return {
                    "success": False,
                    "message": "无效的用户"
                }, 401

            return get_user_race(user_id)
        except Exception as e:
            return {
                "success": False,
                "message": f"获取用户比赛失败: {str(e)}"
            }, 500


@user_info_ns.route('/user-change-password')
class ChangePassword(Resource):
    @user_info_ns.doc(security='Bearer', description='修改用户密码')
    @user_info_ns.expect(password_change_model)
    @optional_login
    def post(self):
        """修改用户密码"""
        try:
            user_id = getattr(g, 'current_user_id', None)
            data = request.get_json()
            old_password = data.get('old_password')
            new_password = data.get('new_password')
            re_new_password = data.get('re_new_password')

            if user_id is None:
                return {
                    "success": False,
                    "message": "无效的用户"
                }, 401

            return to_chance_password(user_id, old_password, new_password, re_new_password)

        except Exception as e:
            return {
                "success": False,
                "message": f"修改密码失败: {str(e)}"
            }, 500


@user_info_ns.route('/user-change-username')
class ChangeUsername(Resource):
    @user_info_ns.expect(username_change_model)
    @optional_login
    def post(self):
        """修改用户名"""
        try:
            user_id = getattr(g, 'current_user_id', None)
            data = request.get_json()
            new_username = data.get('new_username')

            if user_id is None:
                return {
                    "success": False,
                    "message": "无效的用户"
                }, 401

            return to_change_username(user_id, new_username)
        except Exception as e:
            return {
                "success": False,
                "message": f"修改用户名失败: {str(e)}"
            }, 500


@user_info_ns.route('/user-change-email')
class ChangeEmail(Resource):
    @user_info_ns.expect(email_change_model)
    @optional_login
    def post(self):
        """修改邮箱"""
        try:
            user_id = getattr(g, 'current_user_id', None)
            data = request.get_json()
            new_email = data.get('new_email')
            new_email_code = data.get('new_email_code')

            if user_id is None:
                return {
                    "success": False,
                    "message": "无效的用户"
                }, 401

            return to_change_email(user_id, new_email, new_email_code)
        except Exception as e:
            return {
                "success": False,
                "message": f"修改邮箱失败: {str(e)}"
            }, 500


@user_info_ns.route('/get-username/<int:user_id>')
class GetUsername(Resource):
    @user_info_ns.doc(description='获取用户名')
    @role_required('admin')
    def get(self, user_id):
        """获取用户名"""
        try:
            return get_username(user_id)
        except Exception as e:
            return {
                "success": False,
                "message": f"获取用户名失败: {str(e)}"
            }, 500
