from flask import Blueprint, request, jsonify
from flask_socketio import emit, join_room, leave_room
from flask_jwt_extended import jwt_required, get_jwt_identity
from bson import ObjectId
from datetime import datetime
from database import db  # Import db from database.py
from auth import role_required  # Import role_required from auth.py
from extensions import socketio  # Import socketio from extensions.py

chat_bp = Blueprint("chat", __name__)


@chat_bp.route("/messages", methods=["POST"])
@jwt_required()
def post_message():
    user_id = get_jwt_identity()
    data = request.json
    class_id = ObjectId(data["classId"])
    message = data["message"]

    if not (db.classes.find_one({"_id": class_id, "teacherId": ObjectId(user_id)}) or
            db.classMembers.find_one({"classId": class_id, "studentId": ObjectId(user_id)})):
        return jsonify({"error": "Unauthorized"}), 403

    chat_message = {
        "classId": class_id,
        "userId": ObjectId(user_id),
        "message": message,
        "timestamp": datetime.utcnow()
    }
    db.chatMessages.insert_one(chat_message)
    socketio.emit("new_message", chat_message, room=str(class_id))
    return jsonify({"message": "Posted"}), 201


@chat_bp.route("/messages/<class_id>", methods=["GET"])
@jwt_required()
def get_messages(class_id):
    user_id = get_jwt_identity()
    class_id = ObjectId(class_id)

    if not (db.classes.find_one({"_id": class_id, "teacherId": ObjectId(user_id)}) or
            db.classMembers.find_one({"classId": class_id, "studentId": ObjectId(user_id)})):
        return jsonify({"error": "Unauthorized"}), 403

    messages = db.chatMessages.find({"classId": class_id}).sort("timestamp", 1)
    return jsonify([{"user_id": str(m["userId"]), "message": m["message"], "timestamp": m["timestamp"].isoformat()} for m in messages]), 200


@socketio.on("join")
def on_join(data):
    class_id = data["classId"]
    join_room(class_id)


@socketio.on("leave")
def on_leave(data):
    class_id = data["classId"]
    leave_room(class_id)
