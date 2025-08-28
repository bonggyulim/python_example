# models.py
from datetime import datetime
from flask_sqlalchemy import SQLAlchemy

db = SQLAlchemy()

class Note(db.Model):
    __tablename__ = 'notes'
    id = db.Column(db.Integer, primary_key=True, autoincrement=True) # ID는 자동 증가
    title = db.Column(db.String(255), nullable=False, default="")
    content = db.Column(db.Text, nullable=False, default="")
    summarize = db.Column(db.Text, nullable=False, default="")  # 요약 필드 추가
    sentiment = db.Column(db.Float, nullable=False, default=0.0)  # 감정 점수 필드 추가
    created_date = db.Column(db.Text, nullable=False, default="") # ISO 8601 문자열로 저장
