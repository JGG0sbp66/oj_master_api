from app import redis_wrapper
from app.models import User, QuestionsData, RaceData


def get_stats():
    # 统计注册用户数
    users_count = User.query.count()

    # 统计题目数量
    questions_count = QuestionsData.query.count()

    # 统计竞赛数量
    race_count = RaceData.query.count()

    # 返回统计结果
    return {
        "success": True,
        "注册用户数量": users_count,
        "题目数量": questions_count,
        "竞赛数量": race_count,
        "在线用户数": len(redis_wrapper.keys("online:*"))
    }
