# app.py
import os
from flask import Flask, jsonify, request, abort
from flask_cors import CORS
from models import db, Note
from note_summarize_model import summarize_text
from sentiment_model import classify_sentiment
from sqlalchemy.exc import IntegrityError

def create_app():
    app = Flask(__name__)

    # 간단히 SQLite 파일 사용 (운영은 별도 DB 권장)
    db_path = os.environ.get("DB_PATH", "sqlite:///notes.db")
    app.config["SQLALCHEMY_DATABASE_URI"] = db_path
    app.config["SQLALCHEMY_TRACK_MODIFICATIONS"] = False

    db.init_app(app)
    CORS(app, resources={r"/notes*": {"origins": "*"}})  # 개발 편의용. 운영에선 origin 제한

    with app.app_context():
        db.create_all()

    # DTO ↔ 서버 필드 매핑 헬퍼
    def to_dto(note: Note):
        return {
            "id": note.id,
            "title": note.title,
            "content": note.content,
            "summarize": note.summarize,
            "sentiment": note.sentiment,
            "createdDate": note.createdDate # ISO 8601 문자열
        }

    # [C] Create
    @app.post("/notes")
    def create_note():
        data = request.get_json(silent=True) or {}
        data.pop("id", None)  # 클라이언트가 ID를 보내면 무시

        try:
            summary = summarize_text(data.get("content", "")) or ""
        except:
            summary = ""

        try:
            sentiment = float(classify_sentiment(data.get("content", "")))
        except:
            sentiment = 0.0
        
        note = Note(
            title=data.get("title", ""),
            content=data.get("content", ""),
            summarize=summary,
            sentiment=sentiment,
            createdDate=data.get("createdDate", "")
        )

        db.session.add(note)

        try:
            db.session.commit()
        except IntegrityError:
            db.session.rollback()
            return jsonify({"message": "Integrity error"}), 409
        return jsonify({
            "id": note.id,  # 서버가 생성한 PK
            "title": note.title,
            "content": note.content,
            "createdDate": note.createdDate
        })
        

    # [R] Read all (간단 목록)
    @app.get("/notes")
    def list_notes():
        notes = Note.query.order_by(Note.id.desc()).all()
        return jsonify([to_dto(n) for n in notes])

    # [R] Read one
    @app.get("/notes/<int:note_id>")
    def get_note(note_id: int):
        note = Note.query.get(note_id)
        if not note:
            abort(404, description="Note not found")
        return jsonify(to_dto(note))

    # [U] Update
    @app.put("/notes/<int:note_id>")
    def update_note(note_id: int):
        note = Note.query.get(note_id)
        if not note:
            abort(404, description="Note not found")

        data = request.get_json(silent=True) or {}
        # 부분 수정 허용
        if "title" in data: note.title = data["title"] or ""
        if "content" in data: note.content = data["content"] or ""
        if "createdDate" in data: note.createdDate = data["createdDate"] or ""

        db.session.commit()
        return jsonify(to_dto(note))
        

    # [D] Delete
    @app.delete("/notes/<int:note_id>")
    def delete_note(note_id: int):
        note = Note.query.get(note_id)
        if not note:
            abort(404, description="Note not found")
        db.session.delete(note)
        db.session.commit()
        return ""

    return app

if __name__ == "__main__":
    app = create_app()
    from waitress import serve
    # 개발 서버
    app.run(host="0.0.0.0", port=8080)
