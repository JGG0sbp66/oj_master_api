import json
import smtplib
from datetime import datetime, timedelta
from email.mime.multipart import MIMEMultipart
from email.mime.text import MIMEText

from flask import current_app as app
from .turnstile_service import SMTP_CONFIG
from .. import db
from ..models import RaceData, QuestionsData, UserQuestionStatus, RaceRank, User
from ..utils.validators import BusinessException, render_email_template


def get_race_info(race_id, user_id=None):
    """获取比赛信息（支持游客模式）"""
    race = RaceData.query.filter_by(uid=race_id).first()
    if not race:
        return {"error": "比赛不存在"}, 404

    # 获取题目状态（仅登录用户）
    problem_statuses = {}
    if user_id and race.problems_list:
        statuses = UserQuestionStatus.query.filter(
            UserQuestionStatus.user_id == user_id,
            UserQuestionStatus.question_id.in_(race.problems_list),
            UserQuestionStatus.race_id == race_id
        ).all()
        problem_statuses = {s.question_id: s.state for s in statuses}

    # 获取全局统计信息（user_id=0表示全局数据）
    global_stats = {}
    if race.problems_list:
        stats = UserQuestionStatus.query.filter(
            UserQuestionStatus.user_id == 0,
            UserQuestionStatus.question_id.in_(race.problems_list),
            UserQuestionStatus.race_id == race_id
        ).all()
        global_stats = {s.question_id: {
            "submit_num": s.submit or 0,
            "solve_num": s.solve or 0,
            "first_blood_user": s.first_blood  # 直接返回UID或None
        } for s in stats}

    # 构建题目信息
    problems_info = []
    if race.problems_list:
        questions = {q.uid: q for q in QuestionsData.query.filter(
            QuestionsData.uid.in_(race.problems_list)
        )}

        for pid in race.problems_list:
            question = questions.get(pid)
            question_data = question.question if question else {}
            stats = global_stats.get(pid, {})
            first_blood_user_uid = stats.get("first_blood_user")
            first_blood_user = User.query.filter_by(uid=first_blood_user_uid).first()

            first_blood_user_info = {}
            if first_blood_user:
                first_blood_user_info = {
                    "uid": first_blood_user.uid,
                    "username": first_blood_user.username
                }

            problems_info.append({
                "uid": pid,  # 添加题目UID
                "title": question_data.get("title", "未知题目"),
                "status": problem_statuses.get(pid, "未尝试") if user_id else "未登录",
                "submit_num": stats.get("submit_num", 0),
                "solve_num": stats.get("solve_num", 0),
                "first_blood_user": first_blood_user_info
            })
    # 判断用户是否报名
    is_registered = "已报名" if user_id and user_id in race.user_list else "未报名"

    return {
        "race_info": {
            "title": race.title,
            "start_time": race.start_time.strftime("%Y-%m-%d %H:%M:%S"),
            "end_time": race.end_time.strftime("%Y-%m-%d %H:%M:%S"),
            "problems": problems_info,
            "user_num": len(race.user_list),
            "user_status": "已登录" if user_id else "游客",
            "tags": race.tags,
            "status": race.status,
            "is_registered": is_registered
        }
    }


def get_race_list():
    update_race_status()
    query = RaceData.query

    # 构建响应
    races = query.all()
    race_list = []

    for r in races:
        race_list.append({
            "race_uid": r.uid,
            "title": r.title,
            "logos": r.logos,
            "startTime": r.start_time.strftime("%Y-%m-%d %H:%M:%S"),
            "endTime": r.end_time.strftime("%Y-%m-%d %H:%M:%S"),
            "duration": r.duration,
            "status": r.status,
            "tags": r.tags
        })

    return {
        "race_info": race_list
    }


def get_race_rank(race_id):
    query = RaceRank.query
    query = query.filter(RaceRank.contest_id == race_id)
    # 添加排序条件：先按解题数量降序，再按罚时升序
    query = query.order_by(RaceRank.total_solved.desc(), RaceRank.total_penalty.asc())
    result = query.all()

    race_rank_list = []
    for r in result:
        # 将 problem_stats 从 JSON 字符串转换为字典
        try:
            problem_stats_dict = json.loads(r.problem_stats) if r.problem_stats else {}
        except json.JSONDecodeError:
            problem_stats_dict = {}

        user = User.query.filter_by(uid=r.user_id).first()

        user_info = {}
        if user:
            user_info = {
                "uid": user.uid,
                "username": user.username
            }

        race_rank_list.append({
            "user_info": user_info,
            "contest_id": r.contest_id,
            "problem_stats": problem_stats_dict,  # 使用转换后的字典
            "total_solved": r.total_solved,
            "total_penalty": r.total_penalty
        })

    return {
        "race_rank": race_rank_list
    }


def register_race(user_id, race_uid):
    """
    比赛报名服务
    :param user_id: 用户ID
    :param race_uid: 比赛ID
    :return: 报名结果
    :raises: BusinessException
    """
    # 1. 验证用户是否存在
    user = User.query.get(user_id)
    if not user:
        raise BusinessException("用户不存在", 404)

    # 2. 验证比赛是否存在
    race = RaceData.query.get(race_uid)
    if not race:
        raise BusinessException("比赛不存在", 404)

    # 3. 检查是否已报名
    if user_id in race.user_list:
        raise BusinessException("您已经报名过该比赛", 400)

    # 4. 检查比赛是否已开始
    if datetime.now() > race.start_time:
        raise BusinessException("比赛已开始，不能报名", 400)

    # 5. 更新用户数据 - 关键修正点
    new_race_entry = {
        "race_uid": race_uid,  # 保持与数据库一致的类型
        "register_time": datetime.now().strftime('%Y-%m-%d %H:%M:%S')
    }

    # 正确更新JSON字段的方法
    if user.race is None:
        user.race = [new_race_entry]
    else:
        # 创建全新的列表对象确保SQLAlchemy检测到变更
        updated_races = list(user.race)
        updated_races.append(new_race_entry)
        user.race = updated_races

    # 6. 更新比赛数据
    if race.user_list is None:
        race.user_list = [user_id]
    else:
        # 同样确保创建新列表
        updated_users = list(race.user_list)
        if user_id not in updated_users:
            updated_users.append(user_id)
            race.user_list = updated_users

    # 7. 提交事务
    try:
        db.session.commit()
        return {
            "success": True,
            "message": "报名成功",
            "data": {
                "race_uid": race_uid,
                "register_time": new_race_entry['register_time']
            }
        }
    except Exception as e:
        db.session.rollback()
        raise BusinessException(f"数据库操作失败: {str(e)}", 500)


def update_race_rank(user_id, question_uid, is_passed, race_id):
    """
    更新比赛排行榜

    :param user_id: 用户ID
    :param question_uid: 题目ID
    :param is_passed: 是否通过
    :param race_id: 比赛ID
    :return: 字典包含 success, message 和 data 字段
    """
    try:
        # 1. 获取比赛数据
        race = RaceData.query.get(race_id)
        if not race:
            return {
                "success": False,
                "message": f"比赛不存在: {race_id}",
                "data": None
            }

        # 2. 处理 problems_list 数据格式
        if isinstance(race.problems_list, str):
            try:
                race.problems_list = json.loads(race.problems_list)
            except json.JSONDecodeError as e:
                return {
                    "success": False,
                    "message": f"比赛题目列表格式错误: {str(e)}",
                    "data": None
                }

        # 3. 获取题目字母标识
        ALPHABET = 'ABCDEFGHIJKLMNOPQRSTUVWXYZ'
        try:
            question_uid = int(question_uid)  # 确保类型一致
            problem_index = race.problems_list.index(question_uid)
            problem_key = ALPHABET[problem_index]
        except ValueError:
            return {
                "success": False,
                "message": f"题目 {question_uid} 不在比赛 {race_id} 的题目列表中",
                "data": None
            }
        except IndexError:
            return {
                "success": False,
                "message": "题目数量超过字母表范围 (最大26题)",
                "data": None
            }

        # 4. 获取或创建排行榜记录
        rank = RaceRank.query.filter_by(
            contest_id=race_id,
            user_id=user_id
        ).first()

        current_time = datetime.now()

        if not rank:
            # 初始化新记录
            rank = RaceRank(
                contest_id=race_id,
                user_id=user_id,
                problem_stats=json.dumps({}),  # 初始化为空JSON对象
                total_solved=0,
                total_penalty=0
            )
            db.session.add(rank)
            db.session.flush()  # 生成ID但不提交事务

        # 5. 解析当前题目状态
        try:
            problem_stats = json.loads(rank.problem_stats) if isinstance(rank.problem_stats,
                                                                         str) else rank.problem_stats
            if not isinstance(problem_stats, dict):
                problem_stats = {}
        except json.JSONDecodeError as e:
            problem_stats = {}
            print(f"解析problem_stats出错: {str(e)}")

        # 6. 初始化题目状态(如果不存在)
        if problem_key not in problem_stats:
            problem_stats[problem_key] = {
                "solved": False,
                "submit_count": 0,
                "penalty_time": 0,
                "first_solve_time": None
            }

        # 7. 更新提交次数
        problem_stats[problem_key]["submit_count"] += 1

        # 8. 处理通过情况
        if is_passed and not problem_stats[problem_key]["solved"]:
            # 计算罚时(分钟): 解题时间 + 错误提交次数*20
            time_diff = (current_time - race.start_time).total_seconds() / 60
            penalty_time = round(time_diff + (problem_stats[problem_key]["submit_count"] - 1) * 20, 2)  # 保留2位小数

            problem_stats[problem_key].update({
                "solved": True,
                "penalty_time": penalty_time,
                "first_solve_time": current_time.strftime("%Y-%m-%d %H:%M:%S")
            })

            # 更新总解题数和总罚时
            rank.total_solved += 1
            rank.total_penalty += penalty_time

        # 9. 序列化并保存数据
        try:
            # 使用紧凑的JSON格式(无额外空格)
            rank.problem_stats = json.dumps(
                problem_stats,
                ensure_ascii=False,
                separators=(',', ':')
            )
        except (TypeError, ValueError) as e:
            db.session.rollback()
            return {
                "success": False,
                "message": f"无法序列化题目状态数据: {str(e)}",
                "data": None
            }

        # 10. 提交事务
        db.session.commit()

        return {
            "success": True,
            "message": "排行榜更新成功",
            "data": {
                "contest_id": race_id,
                "user_id": user_id,
                "problem_key": problem_key,
                "problem_stats": problem_stats[problem_key],
                "total_solved": rank.total_solved,
                "total_penalty": rank.total_penalty
            }
        }

    except Exception as e:
        db.session.rollback()
        return {
            "success": False,
            "message": f"更新排行榜失败: {str(e)}",
            "data": None,
            "error": str(e)
        }


def validate_race_access(user_id, race_id):
    """
    验证用户是否有权限使用该比赛的AI评判功能
    :param user_id: 用户ID
    :param race_id: 比赛ID
    :return: (是否通过验证, 错误信息, HTTP状态码)
    """
    if race_id <= 0:
        return True, None, None  # 非比赛问题直接通过

    # 检查比赛是否存在
    race = RaceData.query.get(race_id)

    if not race:
        return False, "比赛不存在", 404

    # 检查比赛是否已结束
    if race.status == 'ended':
        return False, "比赛已结束，无法提交", 403

    if race.status == 'upcoming':
        return False, "比赛未开始，无法提交", 403

    # 检查用户是否在报名列表中
    user_list = race.user_list or []
    if user_id not in user_list:  # 注意user_list可能是字符串ID列表
        return False, "未报名该比赛，无法提交", 403

    return True, None, None


def update_race_status():
    """比赛状态更新"""
    try:
        now = datetime.now()

        # 1. 更新进行中的比赛
        RaceData.query.filter(
            RaceData.start_time <= now,
            RaceData.end_time > now,
            RaceData.status != 'running'
        ).update({'status': 'running'})

        # 2. 更新已结束的比赛
        RaceData.query.filter(
            RaceData.end_time <= now,
            RaceData.status != 'ended'
        ).update({'status': 'ended'})

        db.session.commit()
        return True
    except Exception as e:
        db.session.rollback()
        raise e


def get_start_race_list():
    """获取即将开始的比赛列表"""
    now = datetime.now()
    reminder_minutes = 30
    reminder_time = now + timedelta(minutes=reminder_minutes)
    # 1. 获取30分钟后开始的比赛
    upcoming_races = RaceData.query.filter(
        RaceData.start_time > now,
        RaceData.start_time <= reminder_time,
        RaceData.status == 'upcoming'
    ).all()

    result_list = []

    for race in upcoming_races:
        race_dict = {
            "title": race.title,
            "start_time": race.start_time.strftime("%Y-%m-%d %H:%M:%S"),
            "duration": race.duration,
            "tags": [tag['name'] for tag in race.tags],
            "user_list": race.user_list,
        }
        result_list.append(race_dict)

    return result_list


def send_race_email(to_email, title, start_time, duration, tags):
    """发送比赛即将开始验证码邮件"""
    sender = SMTP_CONFIG["user"]

    try:
        html_content = render_email_template("match_reminder.html", contest_name=title, start_time=start_time,
                                             duration=duration, contest_type=tags)

        msg = MIMEMultipart('alternative')
        msg['From'] = sender
        msg['To'] = to_email
        msg['Subject'] = "比赛即将开始 - 请及时参赛"

        msg.attach(MIMEText(html_content, 'html'))
        msg.attach(MIMEText(f"您参加的比赛{title}即将在30分钟后开始，请及时参赛。", 'plain'))

        with smtplib.SMTP_SSL(SMTP_CONFIG["host"], SMTP_CONFIG["port"]) as server:
            server.login(sender, SMTP_CONFIG["password"])
            server.sendmail(sender, [to_email], msg.as_string())

        app.logger.info(f"邮件发送成功: {to_email}")
        return True

    except Exception as e:
        app.logger.error(f"邮件发送失败到 {to_email}: {str(e)}")
        return False


def race_reminder():
    """比赛提醒服务"""
    try:
        upcoming_races = get_start_race_list()
        if not upcoming_races:
            app.logger.info("没有即将开始的比赛")
            return {
                "success": False,
                "message": "没有即将开始的比赛"
            }

        user_ids = [uid for race in upcoming_races for uid in race['user_list']]
        users = {u.uid: u for u in User.query.filter(User.uid.in_(user_ids)).all()}

        emails_to_send = []
        for race in upcoming_races:
            for user_id in race['user_list']:
                if user := users.get(user_id):
                    emails_to_send.append({
                        "to_email": user.email,
                        "title": race['title'],
                        "start_time": race['start_time'],
                        "duration": race['duration'],
                        "tags": race['tags']
                    })

        success_count = 0
        with smtplib.SMTP_SSL(SMTP_CONFIG["host"], SMTP_CONFIG["port"]) as server:
            server.login(SMTP_CONFIG["user"], SMTP_CONFIG["password"])
            for email_data in emails_to_send:
                if send_race_email(**email_data):
                    success_count += 1

        app.logger.info(f"邮件发送完成: 成功{success_count}/总共{len(emails_to_send)}")
        return {
            "success": success_count == len(emails_to_send),
            "total": len(emails_to_send),
            "success_count": success_count
        }

    except Exception as e:
        app.logger.error(f"提醒服务失败: {str(e)}", exc_info=True)
        return False
