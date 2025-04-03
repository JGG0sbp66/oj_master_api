from flask import jsonify
from sqlalchemy import and_, or_
from ..models import Questions
import math


def get_questions(page, category, topic, textinput):
    limit = 15
    offset = (page - 1) * limit

    # 创建基础查询
    query = Questions.query

    # 动态添加过滤条件
    if category and category != "all":
        query = query.filter(Questions.state == category)

    if topic and topic != "all":
        query = query.filter(Questions.topic == topic)

    if textinput:
        query = query.filter(Questions.title.like(f"%{textinput}%"))

    # 获取总记录数（在分页前）
    total_count = query.count()

    # 应用分页
    result = query.limit(limit).offset(offset).all()

    question_list = []
    for q in result:
        question_list.append({
            "uid": q.uid,
            "state": q.state,
            "title": q.title,
            "topic": q.topic,
            "submit_num": q.submit_num,
            "solve_num": q.solve_num,
            "pass_rate": q.pass_rate
        })

    # 计算总页数（基于总记录数）
    total_page = math.ceil(total_count / limit) if total_count > 0 else 1

    return jsonify({
        "questions": question_list,
        "total_page": total_page,
        "total_count": total_count  # 可选：返回总记录数
    })