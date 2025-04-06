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


def get_race_list():
    query = RaceData.query

    # 获取分页结果
    total_count = query.count()
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