from flask import jsonify
from ..models import RaceData


def get_race_info(uid):
    # 创建基础查询
    query = RaceData.query
    # 动态添加过滤条件

    query = query.filter(RaceData.uid == uid)
    result = query.all()

    race_info_list = []
    for r in result:
        race_info_list.append({
            "uid": r.uid,
            "title": r.title,
            "logos": r.logos,
            "start_time": r.start_time,
            "end_time": r.end_time,
            "duration": r.duration,
            "tags": r.tags,
            "created_at": r.created_at,
            "updated_at": r.updated_at,
            "problems_list": r.problems_list,
            "user_list": r.user_list
        })

    return jsonify({
        "race_info": race_info_list
    })
