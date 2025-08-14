#models.py

from datetime import datetime, timezone
from flask_sqlalchemy import SQLAlchemy

db = SQLAlchemy()

class Note(db.Model):
    __tablename__ = 'notes'
    id = db.Column(db.Integer, primary_key=True, autoincrement=True)
    title = db.Column(db.String(255), nullable=False, default="")
    content = db.Column(db.Text, nullable=False, default="")
    created_date = db.Column(db.String(32), nullable=False, default="")