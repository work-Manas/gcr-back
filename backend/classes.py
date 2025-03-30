from flask import Blueprint, request, jsonify
from bson import ObjectId
from datetime import datetime
import random
import string
from database import db  # Import db from database.py
from auth import role_required  # Import role_required from auth.py
from flask_jwt_extended import get_jwt_identity  # Import get_jwt_identity
from imgen import generate_banner

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

    # generate the banner image using the subject
    light_img, dark_img = generate_banner(subject)
    class_data = {
        "subject": subject,
        "code": code,
        "teacherId": ObjectId(user_id),
        "created_at": datetime.utcnow(),
        "bannerLight": light_img,
        "bannerDark": dark_img
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


@classes_bp.route("/student", methods=["GET"])
@role_required("student")
def get_student_classes():
    user_id = get_jwt_identity()
    memberships = db.classMembers.find({"studentId": ObjectId(user_id)})
    classes = []
    for membership in memberships:
        class_doc = db.classes.find_one({"_id": membership["classId"]})
        if class_doc:
            classes.append({
                "class_id": str(class_doc["_id"]),
                "subject": class_doc["subject"],
                "code": class_doc["code"]
            })
    return jsonify({"classes": classes}), 200


@classes_bp.route("/teacher", methods=["GET"])
@role_required("teacher")
def get_teacher_classes():
    user_id = get_jwt_identity()
    classes = db.classes.find({"teacherId": ObjectId(user_id)})
    class_list = []
    for class_doc in classes:
        class_list.append({
            "class_id": str(class_doc["_id"]),
            "subject": class_doc["subject"],
            "code": class_doc["code"]
        })
    return jsonify({"classes": class_list}), 200
