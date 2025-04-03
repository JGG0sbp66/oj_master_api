from .extensions import db
from datetime import datetime


class User(db.Model):
    __tablename__ = 'user_data'
    uid = db.Column(db.Integer, primary_key=True)
    username = db.Column(db.String(80), unique=True, nullable=False)
    password = db.Column(db.String(120), nullable=False)


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
    first_blood = db.Column(db.String(255), nullable=False)


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
