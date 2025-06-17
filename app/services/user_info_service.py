import re

import bcrypt
import requests
from flask import send_from_directory, current_app
from sqlalchemy import func

from ..extensions import db
from app.models import User, QuestionsData, RaceRank, RaceData
from app.utils.validators import is_safe_filename
from config import Config
import os


# def get_avatar_service(user_id):
#     """支持多格式的头像获取服务"""
#     # 检查默认头像是否存在
#     if not os.path.exists(os.path.join(Config.AVATAR_UPLOAD_DIR, Config.DEFAULT_AVATAR)):
#         return {"success": False, "message": "默认头像不存在"}, 404
#
#     # 用户未登录/未指定用户ID时返回默认头像
#     if user_id is None:
#         return send_avatar_file(Config.DEFAULT_AVATAR)
#
#     # 尝试查找用户头像（支持多种格式）
#     avatar_filename = find_user_avatar(user_id)
#     return send_avatar_file(avatar_filename or Config.DEFAULT_AVATAR)

def get_avatar_service(user_id):
    """支持多格式的头像获取服务（如果头像不存在，不返回默认头像，前端自行处理）"""
    # 用户未登录/未指定用户ID时直接返回404（前端处理）
    if user_id is None:
        return {"success": False, "message": "未提供用户ID"}, 404

    # 尝试查找用户头像（支持多种格式）
    avatar_filename = find_user_avatar(user_id)

    # 如果找到用户头像就返回，否则404（前端会自行生成）
    if avatar_filename:
        return send_avatar_file(avatar_filename)
    return {"success": False, "message": "头像不存在"}, 404


def send_avatar_file(filename):
    """安全发送头像文件"""
    if not is_safe_filename(filename):
        return {"success": False, "message": "非法文件名"}, 400

    try:
        return send_from_directory(
            directory=Config.AVATAR_UPLOAD_DIR,
            path=filename,
            max_age=3600
        )
    except FileNotFoundError:
        return {"success": False, "message": "头像文件不存在"}, 404


def find_user_avatar(user_id):
    """查找用户可能存在的头像文件（支持多格式）"""
    for ext in Config.ALLOWED_AVATAR_EXTENSIONS:
        filename = f"{user_id}.{ext}"
        filepath = os.path.join(Config.AVATAR_UPLOAD_DIR, filename)
        if os.path.exists(filepath):
            return filename
    return None


def save_avatar(user_id, file):
    """保存用户上传的头像（自动处理格式）"""
    # 获取安全的文件扩展名
    file_ext = file.filename.rsplit('.', 1)[1].lower()
    if file_ext not in Config.ALLOWED_AVATAR_EXTENSIONS:
        raise ValueError("不支持的文件类型")

    # 删除用户旧头像（所有格式）
    delete_old_avatars(user_id)

    # 保存新头像（格式统一为user_id.ext）
    filename = f"{user_id}.{file_ext}"
    file.save(os.path.join(Config.AVATAR_UPLOAD_DIR, filename))
    return filename


def delete_old_avatars(user_id):
    """删除用户所有格式的旧头像"""
    for ext in Config.ALLOWED_AVATAR_EXTENSIONS:
        old_file = os.path.join(Config.AVATAR_UPLOAD_DIR, f"{user_id}.{ext}")
        try:
            os.remove(old_file)
        except FileNotFoundError:
            pass


def get_user_info(user_id):
    """获取用户信息（包括用户名、邮箱）"""
    user = User.query.get(user_id)
    if not user:
        return None

    return {
        "username": user.username,
        "email": user.email,
        "description": user.description,
        "questions_num": len(user.questions),
        "races_num": len(user.race),
        "create_time": user.create_time.strftime('%Y-%m-%d'),
        "rating": user.rating,
    }


def get_user_questions(user_id, limit=10):
    """
    获取用户最近做的题目（带题目详情）

    参数:
        user_id: 用户ID
        limit: 返回记录数（默认10条）
    """
    # 1. 获取用户做题记录
    user = User.query.get(user_id)
    if not user or not user.questions:
        return []

    # 2. 提取最近的题目UID和时间
    sorted_questions = sorted(
        user.questions,
        key=lambda x: x['submit_time'],
        reverse=True
    )[:limit]

    # 3. 获取题目详细信息
    question_uids = [q['question_uid'] for q in sorted_questions]
    questions_data = QuestionsData.query.filter(
        QuestionsData.uid.in_(question_uids)
    ).all()

    # 4. 构建结果
    result = []
    for user_record in sorted_questions:
        # 找到对应的题目详情
        detail = next(
            (qd for qd in questions_data
             if str(qd.uid) == user_record['question_uid']),
            None
        )
        if detail:
            result.append({
                "submit_time": user_record['submit_time'],
                "title": detail.question.get('title'),
                "topic": str(detail.topic),
                "question_uid": user_record['question_uid']
            })

    return result


def get_user_race(user_id, limit=10):
    """
    获取用户最近报名的比赛（带比赛详情和排名信息）

    参数:
        user_id: 用户ID
        limit: 返回记录数（默认10条）
    返回:
        [{
            "register_time": "报名时间",
            "title": "比赛标题",
            "start_time": "开始时间",
            "end_time": "结束时间",
            "race_uid": "比赛ID",
            "status": "比赛状态",
            "ranking": {
                "rank": 排名,
                "total_solved": 解题数,
                "total_penalty": 总罚时,
                "problem_stats": 题目详情,
                "total_participants": 总参赛人数
            }
        }]
    """
    result = []  # 初始化结果列表

    try:
        # 1. 获取用户比赛报名记录
        user = User.query.get(user_id)
        if not user or not user.race:
            return []

        # 2. 提取最近的比赛记录
        sorted_races = sorted(
            user.race,
            key=lambda x: x['register_time'],
            reverse=True
        )[:limit]

        # 3. 获取比赛详细信息
        race_uids = [r['race_uid'] for r in sorted_races]
        races_data = RaceData.query.filter(
            RaceData.uid.in_(race_uids)
        ).all()

        # 4. 构建结果
        for user_record in sorted_races:
            # 找到对应的比赛详情
            detail = next(
                (rd for rd in races_data
                 if str(rd.uid) == user_record['race_uid']),
                None
            )
            if detail:
                # 获取排名信息
                ranking = None
                rank_record = RaceRank.query.filter_by(
                    user_id=user_id,
                    contest_id=int(user_record['race_uid'])
                ).first()

                if rank_record:
                    ranking = get_user_race_ranking(user_id, int(user_record['race_uid']))

                race_entry = {
                    "register_time": user_record['register_time'],
                    "title": detail.title,
                    "start_time": detail.start_time.strftime('%Y-%m-%d %H:%M:%S'),
                    "end_time": detail.end_time.strftime('%Y-%m-%d %H:%M:%S'),
                    "race_uid": user_record['race_uid'],
                    "status": detail.status,
                    "ranking": ranking  # 可能为None如果用户未参赛
                }
                result.append(race_entry)

        return result

    except Exception as e:
        current_app.logger.error(f"获取用户比赛记录失败: {str(e)}")
        return []  # 返回空列表而不是抛出异常，更友好


def get_user_race_ranking(user_id, contest_id):
    """
    获取用户在指定比赛中的排名

    参数:
        user_id: 用户ID
        contest_id: 比赛ID
    返回:
        {
            "rank": 排名,
            "total_solved": 解题数,
            "total_penalty": 总罚时,
            "problem_stats": 题目详情,
            "total_participants": 总参赛人数
        }
    """
    # 1. 获取该比赛的所有参赛者排名数据
    all_ranks = RaceRank.query.filter_by(contest_id=contest_id).all()

    # 2. 按规则排序
    sorted_ranks = sorted(
        all_ranks,
        key=lambda x: (-x.total_solved, x.total_penalty)
    )

    # 3. 计算排名（考虑并列情况）
    current_rank = 1
    ranks = []
    for i, rank in enumerate(sorted_ranks):
        # 如果不是第一个，且与前一个成绩不同，则更新current_rank
        if i > 0 and (
                sorted_ranks[i - 1].total_solved != rank.total_solved or
                sorted_ranks[i - 1].total_penalty != rank.total_penalty
        ):
            current_rank = i + 1

        ranks.append({
            "user_id": rank.user_id,
            "rank": current_rank,
            "total_solved": rank.total_solved,
            "total_penalty": rank.total_penalty
        })

    # 4. 查找指定用户的排名
    user_rank = next(
        (r for r in ranks if r['user_id'] == user_id),
        None
    )

    if not user_rank:
        return None

    # 5. 获取完整的用户排名信息
    user_full_info = RaceRank.query.filter_by(
        user_id=user_id,
        contest_id=contest_id
    ).first()

    return {
        "rank": user_rank['rank'],
        "total_solved": user_rank['total_solved'],
        "total_penalty": user_rank['total_penalty'],
        "problem_stats": user_full_info.problem_stats,
        "total_participants": len(sorted_ranks)
    }


def to_chance_password(user_id, old_password, new_password, re_new_password):
    # 1. 参数校验
    if not all([user_id, old_password, new_password, re_new_password]):
        return {
            "success": False,
            "message": "参数错误"
        }

    # 2. 用户存在性检查
    user = User.query.get(user_id)
    if not user:
        return {
            "success": False,
            "message": "用户不存在"
        }

    # 3. 旧密码验证
    try:
        if not bcrypt.checkpw(old_password.encode('utf-8'), user.password.encode('utf-8')):
            return {
                "success": False,
                "message": "旧密码错误"
            }, 401
    except Exception as e:
        return {
            "success": False,
            "message": f"密码验证失败: {str(e)}"
        }, 500

    # 4. 新密码一致性检查
    if new_password != re_new_password:
        return {
            "success": False,
            "message": "新密码不一致"
        }, 400

    # 5. 新密码哈希处理
    try:
        hashed_password = bcrypt.hashpw(new_password.encode('utf-8'), bcrypt.gensalt())
    except Exception as e:
        return {
            "success": False,
            "message": f"密码加密失败: {str(e)}"
        }, 500

    # 6. 更新密码
    try:
        user.password = hashed_password.decode('utf-8')
        db.session.commit()
        return {
            "success": True,
            "message": "密码修改成功"
        }
    except Exception as e:
        db.session.rollback()
        return {
            "success": False,
            "message": f"密码修改失败: {str(e)}"
        }, 500


def to_change_username(user_id, new_username):
    """修改用户名"""
    # 1. 参数校验
    if not all([user_id, new_username]):
        return {
            "success": False,
            "message": "参数错误"
        }, 400

    # 2. 用户存在性检查
    user = User.query.get(user_id)
    if not user:
        return {
            "success": False,
            "message": "用户不存在"
        }, 404

    # 3. 新用户名合法性检查（长度、字符等）
    if not re.match(r'^[a-zA-Z0-9]{5,12}$', new_username):
        return {
            'success': False, 'message': '用户名必须是5-12位字母数字组合'
        }, 400

    # 4. 检查用户名是否已存在（不区分大小写）
    existing_user = User.query.filter(
        func.lower(User.username) == func.lower(new_username),
        User.uid != user_id  # 排除当前用户
    ).first()
    if existing_user:
        return {
            "success": False,
            "message": "用户名已存在"
        }, 409

    # 5. 更新用户名
    try:
        user.username = new_username
        db.session.commit()
        return {
            "success": True,
            "message": "用户名修改成功"
        }
    except Exception as e:
        db.session.rollback()
        return {
            "success": False,
            "message": f"用户名修改失败: {str(e)}"
        }, 500


def to_change_email(user_id, email, email_code):
    """修改邮箱（需验证邮箱验证码）"""
    # 1. 参数校验
    if not all([user_id, email, email_code]):
        return {"success": False, "message": "参数错误"}, 400

    # 2. 用户存在性检查
    user = User.query.get(user_id)
    if not user:
        return {"success": False, "message": "用户不存在"}, 404

    # 3. 检查邮箱是否已被其他用户占用
    # existing_user = User.query.filter(
    #     User.email == email,
    #     User.uid != user_id  # 排除当前用户
    # ).first()
    # if existing_user:
    #     return {"success": False, "message": "邮箱已被占用"}, 409

    # 4. 验证邮箱验证码
    try:
        response = requests.post(
            "http://localhost:5000/api/verify-email-code",
            json={"email": email, "code": email_code},
            headers={"Content-Type": "application/json"}
        )
        result = response.json()
    except Exception as e:
        return {"success": False, "message": f"验证码服务异常: {str(e)}"}, 500

    if not result.get("success"):
        return {"success": False, "message": "邮箱验证码错误或已过期"}, 403

    # 5. 更新邮箱
    try:
        user.email = email
        db.session.commit()
        return {"success": True, "message": "邮箱修改成功"}
    except Exception as e:
        db.session.rollback()
        return {"success": False, "message": f"邮箱修改失败: {str(e)}"}, 500


def to_change_description(user_id, new_description):
    """修改用户描述"""
    # 1. 参数校验
    if not user_id or not new_description:
        return {"success": False, "message": "参数错误"}, 400

    # 2. 用户存在性检查
    user = User.query.get(user_id)
    if not user:
        return {"success": False, "message": "用户不存在"}, 404

    # 3. 更新描述
    try:
        user.description = new_description
        db.session.commit()
        return {"success": True, "message": "个人简介修改成功"}
    except Exception as e:
        db.session.rollback()
        return {"success": False, "message": f"个人简介修改失败: {str(e)}"}, 500


def get_username(uid):
    """获取用户名"""
    # 1. 参数校验
    if not uid:
        return {"success": False, "message": "参数错误"}, 400

    # 2. 用户存在性检查
    user = User.query.get(uid)
    if not user:
        return {"success": False, "message": "用户不存在"}, 404

    # 3. 返回用户名
    return {"success": True, "message": user.username}


def get_user_list_service(uid=None, username=None, rating=None, page=1, per_page=8):
    query = User.query

    # 过滤条件
    if uid:
        query = query.filter(User.id == uid)
    if username:
        query = query.filter(User.username.like(f'%{username}%'))  # 模糊搜索
    if rating:
        query = query.filter(User.rating >= rating)

    # 分页
    paginated_users = query.paginate(page=page, per_page=per_page)

    # 正确处理用户列表
    users = [{
        'uid': user.uid,
        'username': user.username,
        'email': user.email,
        'description': user.description,
        'role': user.role,
        'questions': user.questions,
        'race': user.race,
        'rating': user.rating,
        'create_time': user.create_time.strftime('%Y-%m-%d %H:%M:%S') if user.create_time else None,
        'is_banned': user.is_banned,
        'ban_reason': user.ban_reason,
        'ban_start_time': user.ban_start_time.strftime('%Y-%m-%d %H:%M:%S') if user.ban_start_time else None,
        'ban_end_time': user.ban_end_time.strftime('%Y-%m-%d %H:%M:%S') if user.ban_end_time else None
    } for user in paginated_users.items]  # 这里遍历paginated_users.items

    return {
        "success": True,
        "data": {
            "users": users,
            "total_pages": paginated_users.pages,
            "current_page": page,
            "total_items": paginated_users.total  # 添加总记录数
        }
    }


def ban_user(uid, ban_reason, ban_end_time=None):
    """封禁用户"""
    # 1. 参数校验
    if not uid or not ban_reason:
        return {"success": False, "message": "参数错误"}, 400

    # 2. 用户存在性检查
    user = User.query.get(uid)
    if not user:
        return {"success": False, "message": "用户不存在"}, 404

    # 3. 更新封禁信息
    try:
        user.is_banned = True
        user.ban_reason = ban_reason
        user.ban_start_time = db.func.now()  # 设置封禁开始时间为当前时间
        user.ban_end_time = ban_end_time  # 可以为None表示永久封禁
        db.session.commit()
        return {"success": True, "message": "用户已被封禁"}
    except Exception as e:
        db.session.rollback()
        return {"success": False, "message": f"封禁用户失败: {str(e)}"}, 500


def unban_user(uid):
    """解封用户"""
    # 1. 参数校验
    if not uid:
        return {"success": False, "message": "参数错误"}, 400

    # 2. 用户存在性检查
    user = User.query.get(uid)
    if not user:
        return {"success": False, "message": "用户不存在"}, 404

    # 3. 更新解封信息
    try:
        user.is_banned = False
        db.session.commit()
        return {"success": True, "message": "用户已被解封"}
    except Exception as e:
        db.session.rollback()
        return {"success": False, "message": f"解封用户失败: {str(e)}"}, 500


def update_user_role_service(uid, new_role):
    """更新用户角色"""
    # 1. 参数校验
    if not uid or not new_role:
        return {"success": False, "message": "参数错误"}, 400

    # 2. 用户存在性检查
    user = User.query.get(uid)
    if not user:
        return {"success": False, "message": "用户不存在"}, 404

    # 3. 更新角色
    try:
        user.role = new_role
        db.session.commit()
        return {"success": True, "message": "用户角色已更新"}
    except Exception as e:
        db.session.rollback()
        return {"success": False, "message": f"更新用户角色失败: {str(e)}"}, 500
