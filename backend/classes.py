from flask import Blueprint, request, jsonify
from bson import ObjectId
from datetime import datetime
import random
import string
from database import db  # Import db from database.py
from auth import role_required  # Import role_required from auth.py
from flask_jwt_extended import get_jwt_identity  # Import get_jwt_identity

classes_bp = Blueprint("classes", __name__)


@classes_bp.route("/", methods=["POST"], endpoint="create_class")
@role_required("teacher")
def create_class():
    user_id = get_jwt_identity()
    subject = request.json["subject"]

    while True:
        code = "-".join(["".join(random.choices(string.ascii_lowercase, k=3))
                        for _ in range(3)])
        if not db.classes.find_one({"code": code}):
            break

    class_data = {
        "subject": subject,
        "code": code,
        "teacherId": ObjectId(user_id),
        "created_at": datetime.utcnow()
    }
    class_id = db.classes.insert_one(class_data).inserted_id
    return jsonify({"class_id": str(class_id), "code": code}), 201


@classes_bp.route("/join", methods=["POST"], endpoint="join_class")
@role_required("student")
def join_class():
    user_id = get_jwt_identity()
    code = request.json["code"]
    class_doc = db.classes.find_one({"code": code})

    if not class_doc:
        return jsonify({"error": "Class not found"}), 404

    membership = {"classId": class_doc["_id"], "studentId": ObjectId(user_id)}
    if db.classMembers.find_one(membership):
        return jsonify({"error": "Already enrolled"}), 400

    db.classMembers.insert_one(membership)
    return jsonify({"message": "Joined class"}), 200
