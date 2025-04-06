from .extensions import db
from datetime import datetime


class User(db.Model):
    __tablename__ = 'user_data'

    uid = db.Column(db.Integer, primary_key=True)
    username = db.Column(db.String(80), unique=True, nullable=False)
    password = db.Column(db.String(120), nullable=False)
    role = db.Column(db.String(20), default='user')


class Questions(db.Model):
    __tablename__ = 'questionslist'

    uid = db.Column(db.Integer, primary_key=True)
    state = db.Column(db.String(80), unique=True, nullable=False)
    title = db.Column(db.String(255), nullable=False)
    topic = db.Column(db.String(255), nullable=False)
    submit_num = db.Column(db.Integer, nullable=False)
    solve_num = db.Column(db.Integer, nullable=False)
    pass_rate = db.Column(db.Float, nullable=False)
    description = db.Column(db.String(255), nullable=False)
    pattern_text = db.Column(db.String(255), nullable=False)
    print_text = db.Column(db.String(255), nullable=False)
    test_input = db.Column(db.String(255), nullable=False)
    test_print = db.Column(db.String(255), nullable=False)
    tle = db.Column(db.Integer, nullable=False)
    mle = db.Column(db.Integer, nullable=False)


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
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    updated_at = db.Column(db.DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    problems_list = db.Column(db.JSON, nullable=False)
    user_list = db.Column(db.JSON, nullable=False)
    status = db.Column(db.String(255), nullable=False)


class FirstBloodData(db.Model):
    __tablename__ = 'first_blood_records'

    user_id = db.Column(db.Integer, nullable=False)
    problem_id = db.Column(db.Integer, primary_key=True, nullable=False)
    contest_id = db.Column(db.Integer, primary_key=True, nullable=False)
    solve_time = db.Column(db.DateTime, nullable=False)
