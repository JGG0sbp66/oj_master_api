from app import redis_wrapper, db
from app.models import User, QuestionsData, RaceData, UserHeatmap


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


def get_user_heatmap(user_id, year):
    """
    获取用户的热力图数据
    :param user_id: 用户ID
    :param year: 年份
    :return: 热力图数据
    """

    result = UserHeatmap.query.filter(
            UserHeatmap.user_id == user_id,
            db.extract('year', UserHeatmap.activity_date) == year
        ).order_by(UserHeatmap.activity_date).all()

    return result

def update_user_heatmap(user_id, activity_date):
    """
    更新用户的热力图数据
    :param user_id: 用户ID
    :param activity_date: 活动日期
    :return: None
    """
    heatmap_entry = UserHeatmap.query.filter_by(
        user_id=user_id,
        activity_date=activity_date
    ).first()

    if heatmap_entry:
        # 如果记录存在，分数+1
        heatmap_entry.activity_score += 1
    else:
        # 记录不存在：新建记录（初始分数1）
        heatmap_entry = UserHeatmap(
            user_id=user_id,
            activity_date=activity_date,
            activity_score=1,
        )
        db.session.add(heatmap_entry)

    db.session.commit()