from ..models import UserQuestionStatus, QuestionsData
import math


def get_question_status(user_id, question_id):
    """获取用户对特定题目的状态"""
    status = UserQuestionStatus.query.filter_by(
        user_id=user_id,
        question_id=question_id,
        race_id=0
    ).first()

    return status.state if status else "未尝试"  # 默认状态


def get_user_all_question_statuses(user_id):
    """获取用户所有题目的状态字典（性能优化用）"""
    statuses = UserQuestionStatus.query.filter_by(user_id=user_id, race_id=0).all()
    return {s.question_id: s.state for s in statuses}


def get_questions(page, category, topic, textinput, user_id=None):
    limit = 15
    offset = (page - 1) * limit

    # 基础查询
    query = QuestionsData.query

    # 状态过滤逻辑（根据是否登录）
    if category in ['未尝试', '已通过', '未通过']:
        if user_id:  # 登录用户
            statuses = get_user_all_question_statuses(user_id)
            if category == '未尝试':
                # 查询不在状态表中的题目
                query = query.filter(~QuestionsData.uid.in_(statuses.keys()))
            else:
                # 查询状态为指定值的题目
                filtered_ids = [qid for qid, state in statuses.items() if state == category]
                query = query.filter(QuestionsData.uid.in_(filtered_ids or [0]))
        else:  # 游客
            if category != '未尝试':
                return {
                    "questions": [],
                    "total_page": 1,
                    "total_count": 0
                }

    # 难度筛选
    if topic and topic != "all":
        query = query.filter(QuestionsData.topic == topic)

    # 文本搜索
    if textinput:
        query = query.filter(
            QuestionsData.question['title'].astext.ilike(f"%{textinput}%")
        )

    # 获取分页结果
    total_count = query.count()
    questions = query.limit(limit).offset(offset).all()

    # 获取所有题目ID用于批量查询统计信息
    question_ids = [q.uid for q in questions]

    # 批量获取统计信息（race_id=0, user_id=0）
    stats_query = UserQuestionStatus.query.filter(
        UserQuestionStatus.race_id == 0,
        UserQuestionStatus.user_id == 0,
        UserQuestionStatus.question_id.in_(question_ids)
    ).all()

    stats_dict = {s.question_id: {
        "submit_num": s.submit or 0,
        "solve_num": s.solve or 0
    } for s in stats_query}

    # 构建响应
    question_list = []
    for q in questions:
        question_json = q.question
        stats = stats_dict.get(q.uid, {
            "submit_num": 0,
            "solve_num": 0,
            "pass_rate": 0
        })

        item = {
            "uid": q.uid,
            "title": question_json.get("title"),
            "state": "未尝试",  # 默认值
            "topic": q.topic,
            "submit_num": stats["submit_num"],
            "solve_num": stats["solve_num"]
        }

        if user_id:  # 只有登录用户需要查询真实状态
            statuses = get_user_all_question_statuses(user_id)
            item["state"] = statuses.get(q.uid, "未尝试")

        question_list.append(item)

    return {
        "questions": question_list,
        "total_page": math.ceil(total_count / limit),
        "total_count": total_count
    }


def get_question_detail(question_id):
    item = QuestionsData.query.filter_by(uid=question_id).first_or_404()
    question_json = item.question

    return {
        "title": question_json.get("title"),
        "tle": question_json.get("time_limit", 1000),  # 注意字段名变化
        "mle": question_json.get("memory_limit", 128),
        "description": question_json.get("description"),
        "pattern_text": question_json.get("input_format"),
        "print_text": question_json.get("output_format"),
        "examples": question_json.get("examples", [])
    }
