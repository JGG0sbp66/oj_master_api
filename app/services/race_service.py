from datetime import datetime

from .. import db
from ..models import RaceData, QuestionsData, UserQuestionStatus, RaceRank, User
from ..utils.validators import BusinessException


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

            problems_info.append({
                "uid": pid,  # 添加题目UID
                "title": question_data.get("title", "未知题目"),
                "status": problem_statuses.get(pid, "未尝试") if user_id else "未登录",
                "submit_num": stats.get("submit_num", 0),
                "solve_num": stats.get("solve_num", 0),
                "first_blood_user": stats.get("first_blood_user")
            })

    return {
        "race_info": {
            "title": race.title,
            "start_time": race.start_time.strftime("%Y-%m-%d %H:%M:%S"),
            "end_time": race.end_time.strftime("%Y-%m-%d %H:%M:%S"),
            "problems": problems_info,
            "user_num": len(race.user_list),
            "user_status": "已登录" if user_id else "游客",
            "tags": race.tags
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
    result = query.all()

    race_rank_list = []
    for r in result:
        race_rank_list.append({
            "user_id": r.user_id,
            "contest_id": r.contest_id,
            "problem_stats": r.problem_stats,
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
    user_races = user.race or []
    if any(str(r.get('race_uid')) == str(race_uid) for r in user_races):  # 添加类型转换
        raise BusinessException("您已经报名过该比赛", 400)

    # 4. 检查比赛是否已开始
    if datetime.utcnow() > race.start_time:
        raise BusinessException("比赛已开始，不能报名", 400)

    # 5. 更新用户数据 - 关键修正点
    new_race_entry = {
        "race_uid": race_uid,  # 保持与数据库一致的类型
        "register_time": datetime.utcnow().strftime('%Y-%m-%d %H:%M:%S')
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


def update_race_status():
    """比赛状态更新"""
    try:
        now = datetime.utcnow()

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
