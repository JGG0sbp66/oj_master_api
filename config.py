# config.py
import os
from datetime import timedelta

class Config:
    SECRET_KEY = os.urandom(24)
    SQLALCHEMY_DATABASE_URI = 'mysql+pymysql://root:@localhost:3308/reborn_oj_master'
    SQLALCHEMY_TRACK_MODIFICATIONS = False
    PERMANENT_SESSION_LIFETIME = timedelta(minutes=30)
    TURNSTILE_SECRET_KEY = "0x4AAAAAABC_Oa6dJZB8d7Ql7PRLdDli0Vc"