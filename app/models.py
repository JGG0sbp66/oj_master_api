from .extensions import db
from datetime import datetime


class User(db.Model):
    __tablename__ = 'user_data'

    uid = db.Column(db.Integer, primary_key=True)
    username = db.Column(db.String(80), unique=True, nullable=False)
    password = db.Column(db.String(120), nullable=False)
    email = db.Column(db.String(120), nullable=False)
    description = db.Column(db.Text, nullable=False, default='热爱编程，喜欢解决复杂问题。正在学习算法和数据结构')
    role = db.Column(db.Enum('user', 'admin', 'superAdmin'), nullable=False, default='user')
    questions = db.Column(db.JSON, nullable=True)
    race = db.Column(db.JSON, nullable=True)
    rating = db.Column(db.Integer, nullable=True, default=1500, comment='用户等级积分')
    create_time = db.Column(db.DateTime, default=datetime.now)


class QuestionsData(db.Model):
    __tablename__ = 'questions_data'

    uid = db.Column(db.Integer, primary_key=True)
    question = db.Column(db.JSON, nullable=True)
    topic = db.Column(db.Enum('入门', '普及', '提高', '省选', 'NOI', 'CTSC', name='status_enum'))
    updated_at = db.Column(db.DateTime, default=datetime.now, onupdate=datetime.now)
    is_contest_question = db.Column(db.Boolean, default=False, nullable=False, comment='是否为比赛题目')


class UserQuestionStatus(db.Model):
    __tablename__ = 'user_question_status'

    uid = db.Column(db.Integer, primary_key=True, autoincrement=True, nullable=False, comment='唯一标识')
    race_id = db.Column(db.Integer, primary_key=True, nullable=False, default=0, comment='比赛uid')
    user_id = db.Column(db.Integer, primary_key=True, nullable=False, comment='用户uid')
    question_id = db.Column(db.Integer, primary_key=True, nullable=False, comment='题目uid')
    state = db.Column(db.Enum('未尝试', '已通过', '未通过', name='status_enum'), nullable=False, default='未尝试',
                      comment='作答状态')
    first_blood = db.Column(db.Integer, nullable=True, comment='一血用户的uid')
    submit = db.Column(db.Integer, nullable=True, comment='提交数')
    solve = db.Column(db.Integer, nullable=True, comment='解决数')


class RaceData(db.Model):
    __tablename__ = 'race_data'

    uid = db.Column(db.Integer, primary_key=True, autoincrement=True)
    title = db.Column(db.String(255), nullable=False)
    logos = db.Column(db.JSON, nullable=True)
    start_time = db.Column(db.DateTime, nullable=False)
    end_time = db.Column(db.DateTime, nullable=False)
    duration = db.Column(db.String(20), nullable=True)
    tags = db.Column(db.JSON, nullable=True)
    created_at = db.Column(db.DateTime, default=datetime.now())
    updated_at = db.Column(db.DateTime, default=datetime.now, onupdate=datetime.now)
    problems_list = db.Column(db.JSON, nullable=False)
    user_list = db.Column(db.JSON, nullable=False)
    status = db.Column(db.Enum('upcoming', 'running', 'ended', name='status_enum'), nullable=False, default='upcoming',
                       comment='比赛状态')


class RaceRank(db.Model):
    __tablename__ = 'race_rank'

    user_id = db.Column(db.Integer, primary_key=True, nullable=False)
    contest_id = db.Column(db.Integer, primary_key=True, nullable=False)
    problem_stats = db.Column(db.JSON, nullable=False)
    total_solved = db.Column(db.Integer, nullable=False)
    total_penalty = db.Column(db.Integer, nullable=False)


class UserHeatmap(db.Model):
    __tablename__ = 'user_heatmap'

    user_id = db.Column(db.Integer, primary_key=True, nullable=False)
    activity_date = db.Column(db.DateTime, primary_key=True)
    activity_score = db.Column(db.Integer, nullable=False)
