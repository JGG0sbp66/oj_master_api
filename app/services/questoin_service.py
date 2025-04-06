from ..models import Questions, UserQuestionStatus
import math


def get_question_status(user_id, question_id):
    """获取用户对特定题目的状态"""
    status = UserQuestionStatus.query.filter_by(
        user_id=user_id,
        question_id=question_id,
        race_id = 0
    ).first()

    return status.state if status else "未尝试"  # 默认状态


def get_user_all_question_statuses(user_id):
    """获取用户所有题目的状态字典（性能优化用）"""
    statuses = UserQuestionStatus.query.filter_by(user_id=user_id, race_id =0).all()
    return {s.question_id: s.state for s in statuses}


def get_questions(page, category, topic, textinput, user_id=None):
    limit = 15
    offset = (page - 1) * limit
    query = Questions.query  # 创建基础查询

    # 状态过滤逻辑（根据是否登录）
    if category in ['未尝试', '已通过', '未通过']:
        if user_id:  # 登录用户
            statuses = get_user_all_question_statuses(user_id)
            if category == '未尝试':
                # 查询不在状态表中的题目
                query = query.filter(~Questions.uid.in_(statuses.keys()))
            else:
                # 查询状态为指定值的题目
                filtered_ids = [qid for qid, state in statuses.items() if state == category]
                query = query.filter(Questions.uid.in_(filtered_ids or [0]))
        else:  # 游客
            if category != '未尝试':
                return {
                    "questions": [],
                    "total_page": 1,
                    "total_count": 0
                }

    if topic and topic != "all":
        query = query.filter(Questions.topic == topic)

    if textinput:
        query = query.filter(Questions.title.like(f"%{textinput}%"))

    # 获取分页结果
    total_count = query.count()

    # 构建响应
    questions = query.limit(limit).offset(offset).all()
    question_list = []

    for q in questions:
        item = {
            "uid": q.uid,
            "title": q.title,
            "state": "未尝试",  # 默认值
            "topic": q.topic,
            "submit_num": q.submit_num,
            "solve_num": q.solve_num,
            "pass_rate": q.pass_rate
        }

        if user_id:  # 只有登录用户需要查询真实状态
            statuses = get_user_all_question_statuses(user_id)  # 重新获取状态
            item["state"] = statuses.get(q.uid, "未尝试")

        question_list.append(item)

    return {
        "questions": question_list,
        "total_page": math.ceil(total_count / limit),
        "total_count": total_count
    }
