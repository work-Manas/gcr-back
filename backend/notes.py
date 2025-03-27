from flask import Blueprint, request, jsonify
from bson import ObjectId
from datetime import datetime
from database import db, fs  # Import db and fs from database.py
from flask_jwt_extended import get_jwt_identity  # Import get_jwt_identity
from auth import role_required  # Import role_required from auth.py

notes_bp = Blueprint("notes", __name__)


@notes_bp.route("/", methods=["POST"])
@role_required("teacher")
def upload_notes():
    user_id = get_jwt_identity()
    data = request.form
    class_id = ObjectId(data["classId"])

    if not db.classes.find_one({"_id": class_id, "teacherId": ObjectId(user_id)}):
        return jsonify({"error": "Unauthorized or class not found"}), 403

    title = data["title"]
    content_type = data.get("content_type", "text")

    if content_type == "text":
        content = data["content"]
    elif content_type == "pdf":
        pdf_file = request.files["pdf"]
        content = str(fs.put(pdf_file))
    else:
        return jsonify({"error": "Invalid content type"}), 400

    note = {
        "classId": class_id,
        "teacherId": ObjectId(user_id),
        "title": title,
        "content": content,
        "content_type": content_type,
        "uploaded_at": datetime.utcnow()
    }
    note_id = db.notes.insert_one(note).inserted_id
    return jsonify({"note_id": str(note_id)}), 201
