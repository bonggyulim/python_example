# app.py
import os
import threading
from flask import Flask, jsonify, request, abort, current_app
from flask_cors import CORS
from models import db, Note
from note_summarize_model import summarize_text
from sentiment_model import classify_sentiment
from sqlalchemy.exc import IntegrityError

def create_app():
    app = Flask(__name__)

    # SQLite (개발용)
    db_path = os.environ.get("DB_PATH", "sqlite:///notes.db")
    app.config["SQLALCHEMY_DATABASE_URI"] = db_path
    app.config["SQLALCHEMY_TRACK_MODIFICATIONS"] = False

    db.init_app(app)
    CORS(app, resources={r"/notes*": {"origins": "*"}})

    with app.app_context():
        db.create_all()

    # DTO 변환 (모델: created_date ←→ JSON: createdDate)
    def to_dto(note: Note):
        return {
            "id": note.id,
            "title": note.title,
            "content": note.content,
            "summarize": note.summarize,
            "sentiment": note.sentiment,
            "createdDate": note.created_date,
        }

    # [C] Create
    @app.post("/notes")
    def create_note():
        data = request.get_json(silent=True) or {}
        note = Note(
            title=data.get("title", ""),
            content=data.get("content", ""),
            summarize=None,
            sentiment=None,
            created_date=data.get("createdDate", ""),
        )
        db.session.add(note)
        try:
            db.session.commit()
            # 백그라운드 후처리
            app_obj = current_app._get_current_object()
            threading.Thread(
                target=process_models,
                args=(app_obj, note.id, note.content),
                daemon=True,
            ).start()
        except IntegrityError:
            db.session.rollback()
            return jsonify({"message": "Integrity error"}), 409
        return "", 201

    # 백그라운드: 모델 먼저 계산 → 존재할 때만 UPDATE
    def process_models(app, note_id, content):
        with app.app_context():
            try:
                try:
                    summary = summarize_text(content or "")
                except Exception:
                    summary = None
                try:
                    sentiment = classify_sentiment(content or "")
                except Exception:
                    sentiment = None

                rows = (
                    db.session.query(Note)
                    .filter(Note.id == note_id)
                    .update(
                        {"summarize": summary, "sentiment": sentiment},
                        synchronize_session=False,
                    )
                )
                if rows == 0:
                    db.session.rollback()
                    print(f"[bg] note {note_id} not found (deleted?), skip.")
                    return
                db.session.commit()
            except Exception as e:
                db.session.rollback()
                print(f"[bg] process_models failed: {e}")

    # [R] Read all
    @app.get("/notes")
    def list_notes():
        try:
            notes = db.session.query(Note).order_by(Note.id.desc()).all()
            return jsonify([to_dto(n) for n in notes]), 200
        except Exception:
            return jsonify({"message": "Database error"}), 500

    # [R] Read one  ← ★ 한 번만 정의!
    @app.get("/notes/<int:note_id>")
    def get_note(note_id: int):
        note = db.session.get(Note, note_id)
        if not note:
            abort(404, description="Note not found")
        return jsonify(to_dto(note))

    # [U] Update
    @app.put("/notes/<int:note_id>")
    def update_note(note_id: int):
        note = db.session.get(Note, note_id)
        if not note:
            abort(404, description="Note not found")

        data = request.get_json(silent=True) or {}
        if "title" in data:
            note.title = data["title"] or ""
        if "content" in data:
            note.content = data["content"] or ""
        if "createdDate" in data:
            note.created_date = data["createdDate"] or ""

        db.session.commit()
        return jsonify(to_dto(note))

    # [D] Delete
    @app.delete("/notes/<int:note_id>")
    def delete_note(note_id: int):
        note = db.session.get(Note, note_id)
        if not note:
            abort(404, description="Note not found")
        db.session.delete(note)
        db.session.commit()
        return ""

    return app

if __name__ == "__main__":
    # 개발에서는 app.run, 운영에서는 waitress/gunicorn
    # app.run(host="0.0.0.0", port=8080)
    from waitress import serve
    app = create_app()
    serve(app, host="0.0.0.0", port=8080, threads=1)
