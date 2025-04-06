from flask import jsonify
from ..models import RaceData, Questions, UserQuestionStatus, RaceRank


def get_race_info(race_id, user_id=None):
    """获取比赛信息（支持游客模式）"""
    race = RaceData.query.filter_by(uid=race_id).first()
    if not race:
        return jsonify({"error": "比赛不存在"}), 404

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
        questions = {q.uid: q for q in Questions.query.filter(
            Questions.uid.in_(race.problems_list)
        )}

        for pid in race.problems_list:
            question = questions.get(pid)
            stats = global_stats.get(pid, {})

            problems_info.append({
                "title": question.title if question else "未知题目",
                "status": problem_statuses.get(pid, "未尝试") if user_id else "未登录",
                "submit_num": stats.get("submit_num", 0),
                "solve_num": stats.get("solve_num", 0),
                "first_blood_user": stats.get("first_blood_user")  # 返回UID或None
            })

    return jsonify({
        "race_info": {
            "title": race.title,
            "start_time": race.start_time.strftime("%Y-%m-%d %H:%M:%S"),
            "end_time": race.end_time.strftime("%Y-%m-%d %H:%M:%S"),
            "problems": problems_info,
            "user_num": len(race.user_list),
            "user_status": "已登录" if user_id else "游客"
        }
    })


def get_race_list():
    query = RaceData.query

    # 构建响应
    races = query.all()
    race_list = []

    for r in races:
        race_list.append({
            "title": r.title,
            "logos": r.logos,
            "startTime": r.start_time,
            "endTime": r.end_time,
            "duration": r.duration,
            "status": r.status,
            "tags": r.tags
        })

    return jsonify({
        "race_info": race_list
    })

def get_race_rank(race_id):
    query = RaceRank.query
    # 动态添加过滤条件

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

    return jsonify({
        "race_rank": race_rank_list
    })