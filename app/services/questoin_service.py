from .race_service import update_race_rank
from .. import db
from ..models import UserQuestionStatus, QuestionsData, User
import math
from datetime import datetime


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
            db.func.json_extract(QuestionsData.question, '$.title').ilike(f"%{textinput}%")
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


def add_question_record(user_id, question_uid, is_passed):
    try:
        user = User.query.get(user_id)
        if not user:
            raise ValueError("用户不存在")

        # 初始化
        if user.questions is None:
            user.questions = []

        # 查找是否已有该题目的记录
        existing_index = None
        for i, record in enumerate(user.questions):
            if record["question_uid"] == question_uid:
                existing_index = i
                break

        # 准备记录数据
        new_record = {
            "question_uid": question_uid,
            "submit_time": datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
            "is_passed": is_passed
        }

        # 更新或追加
        if existing_index is not None:
            user.questions[existing_index].update(new_record)
        else:
            user.questions.append(new_record)

        # 标记变更并提交
        from sqlalchemy.orm.attributes import flag_modified
        flag_modified(user, "questions")
        db.session.commit()

        return True
    except Exception as e:
        db.session.rollback()
        raise e


def update_user_question_status(user_id, question_id, is_correct, race_id=0):
    """
    更新用户题目状态到数据库，并处理一血和全局统计记录
    :param user_id: 用户ID
    :param question_id: 题目ID
    :param is_correct: 答案是否正确
    :param race_id: 比赛ID（默认为0表示题库）
    """
    # 检查是否已有用户个人记录
    existing_record = UserQuestionStatus.query.filter_by(
        user_id=user_id,
        question_id=question_id,
        race_id=race_id
    ).first()

    if existing_record:
        # 更新已有记录
        if is_correct:
            existing_record.state = '已通过'
            existing_record.solve = (existing_record.solve or 0) + 1
        else:
            if existing_record.state != '已通过':  # 如果已经是已通过状态则不再降级
                existing_record.state = '未通过'
        existing_record.submit = (existing_record.submit or 0) + 1
    else:
        # 创建新记录
        new_record = UserQuestionStatus(
            race_id=race_id,
            user_id=user_id,
            question_id=question_id,
            state='已通过' if is_correct else '未通过',
            submit=1,
            solve=1 if is_correct else 0
        )
        db.session.add(new_record)

    # 比赛模式下的特殊处理
    if race_id != 0:
        # 获取或创建全局统计记录（user_id=0）
        global_stats = UserQuestionStatus.query.filter_by(
            race_id=race_id,
            question_id=question_id,
            user_id=0  # 全局统计专用
        ).first()

        if not global_stats:
            global_stats = UserQuestionStatus(
                race_id=race_id,
                user_id=0,
                question_id=question_id,
                state='已通过' if is_correct else '未通过',
                submit=0,
                solve=0,
                first_blood=None
            )
            db.session.add(global_stats)
            db.session.flush()  # 确保获得ID

        # 更新全局统计（原子操作）
        if is_correct:
            # 如果是正确答案，更新解决数
            UserQuestionStatus.query.filter_by(
                race_id=race_id,
                question_id=question_id,
                user_id=0
            ).update({
                'submit': UserQuestionStatus.submit + 1,
                'solve': UserQuestionStatus.solve + 1,
                'state': '已通过'
            })

            # 处理一血逻辑（仅在第一次正确解答时）
            if global_stats.first_blood is None:
                global_stats.first_blood = user_id
        else:
            # 如果是错误答案，只更新提交数
            UserQuestionStatus.query.filter_by(
                race_id=race_id,
                question_id=question_id,
                user_id=0
            ).update({
                'submit': UserQuestionStatus.submit + 1
            })

    db.session.commit()


def judge_question(user_id, question_uid, race_id, result):
    try:
        result = result[-10:]
        is_passed = False
        if "答案正确" in result:
            is_passed = True

        add_question_record(user_id, question_uid, is_passed)
        update_user_question_status(user_id, question_uid, is_passed, race_id=race_id)
        if race_id and race_id > 0:
            update_race_rank(user_id, question_uid, is_passed, race_id)

        return {
            "success": True,
            "message": result
        }
    except Exception as e:
        return {
            "success": False,
            "message": f"判题过程中发生错误: {str(e)}"
        }, 500
