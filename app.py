# app.py
import os
from flask import Flask, jsonify, request, abort
from flask_cors import CORS
from models import db, Note
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
            "createdDate": note.created_date,  # Android DTO와 키 맞춤
        }

    # [C] Create
    @app.post("/notes")
    def create_note():
        data = request.get_json(silent=True) or {}
        id_ = data.get("id")
        note = Note(
            id=id_,
            title=data.get("title", ""),
            content=data.get("content", ""),
            created_date=data.get("createdDate") or Note.now_iso()
        )

        db.session.add(note)
        try:
            db.session.commit()
        except IntegrityError:
            db.session.rollback()
            return jsonify({"message": "ID already exists"}), 409
        return jsonify(to_dto(note)), 201
        
    @app.after_request
    def force_close_connection(response):
        response.headers["Connection"] = "close"
        return response

    # [R] Read all (간단 목록)
    @app.get("/notes")
    def list_notes():
        notes = Note.query.order_by(Note.id.desc()).all()
        return jsonify([to_dto(n) for n in notes]), 200

    # [R] Read one
    @app.get("/notes/<int:note_id>")
    def get_note(note_id: int):
        note = Note.query.get(note_id)
        if not note:
            abort(404, description="Note not found")
        return jsonify(to_dto(note)), 200

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
        if "createdDate" in data: note.created_date = data["createdDate"] or ""

        db.session.commit()
        return jsonify(to_dto(note)), 200
        

    # [D] Delete
    @app.delete("/notes/<int:note_id>")
    def delete_note(note_id: int):
        note = Note.query.get(note_id)
        if not note:
            abort(404, description="Note not found")
        db.session.delete(note)
        db.session.commit()
        return "", 204

    return app

if __name__ == "__main__":
    app = create_app()
    # 개발 서버
    app.run(host="0.0.0.0", port=8080, debug=True)
