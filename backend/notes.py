from flask import Blueprint, request, jsonify, send_file
from bson import ObjectId
from datetime import datetime
from io import BytesIO
from database import db, fs  # Import db and fs from database.py
# Import get_jwt_identity and jwt_required
from flask_jwt_extended import get_jwt_identity, jwt_required
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


@notes_bp.route("/class/<class_id>", methods=["GET"])
@jwt_required()
def get_class_notes(class_id):
    user_id = get_jwt_identity()
    class_id = ObjectId(class_id)

    # Check if user is part of the class
    if not (db.classes.find_one({"_id": class_id, "teacherId": ObjectId(user_id)}) or
            db.classMembers.find_one({"classId": class_id, "studentId": ObjectId(user_id)})):
        return jsonify({"error": "Unauthorized or class not found"}), 403

    notes = db.notes.find({"classId": class_id})
    note_list = []
    for note in notes:
        note_data = {
            "note_id": str(note["_id"]),
            "title": note["title"],
            "content_type": note["content_type"]
        }
        if note["content_type"] == "text":
            note_data["content"] = note["content"]
        else:
            note_data["content"] = f"/notes/{note['_id']}/download"
        note_list.append(note_data)
    return jsonify({"notes": note_list}), 200


@notes_bp.route("/<note_id>/download", methods=["GET"])
@jwt_required()
def download_note(note_id):
    user_id = get_jwt_identity()
    note = db.notes.find_one({"_id": ObjectId(note_id)})
    if not note:
        return jsonify({"error": "Note not found"}), 404

    # Check if user is part of the class
    class_id = note["classId"]
    if not (db.classes.find_one({"_id": class_id, "teacherId": ObjectId(user_id)}) or
            db.classMembers.find_one({"classId": class_id, "studentId": ObjectId(user_id)})):
        return jsonify({"error": "Unauthorized"}), 403

    if note["content_type"] != "pdf":
        return jsonify({"error": "Note is not a PDF"}), 400

    file_id = note["content"]
    file_stream = fs.get(ObjectId(file_id))
    return send_file(BytesIO(file_stream.read()), mimetype="application/pdf", as_attachment=True, attachment_filename=f"{note['title']}.pdf")
