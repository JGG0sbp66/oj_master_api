from flask import jsonify
from ..models import FirstBloodData



def get_first_blood(contest_id):
    # 创建基础查询
    query = FirstBloodData.query
    # 动态添加过滤条件

    query = query.filter(contest_id == contest_id)
    result = query.all()

    first_blood_list = []
    for f in result:
        first_blood_list.append({
            "user_id": f.user_id,
            "problem_id": f.problem_id,
            "contest_id": f.contest_id,
            "solve_time": f.solve_time
        })

    return jsonify({
        "first_blood": first_blood_list
    })