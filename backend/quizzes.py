from flask import Blueprint, request, jsonify
from bson import ObjectId
from datetime import datetime
from database import db, fs  # Import db and fs from database.py
from auth import role_required  # Import role_required from auth.py
from pdfminer.high_level import extract_text
from io import BytesIO
from flask_jwt_extended import get_jwt_identity  # Import get_jwt_identity


quizzes_bp = Blueprint("quizzes", __name__)


def generate_quiz_questions(prompt):
    # Placeholder for Gemini API integration
    return [
        {
            "question": "Sample question?",
            "options": ["A", "B", "C", "D"],
            "correct_answer": "B",
            "topics": ["sample_topic"]
        }
    ]


@quizzes_bp.route("/assignments", methods=["POST"])
@role_required("teacher")
def create_quiz_assignment():
    user_id = get_jwt_identity()
    data = request.json
    class_id = ObjectId(data["classId"])

    if not db.classes.find_one({"_id": class_id, "teacherId": ObjectId(user_id)}):
        return jsonify({"error": "Unauthorized or class not found"}), 403

    notes_ids = [ObjectId(nid) for nid in data["notesIds"]]
    deadline = datetime.fromisoformat(data["deadline"])

    quiz_assignment = {
        "classId": class_id,
        "notesIds": notes_ids,
        "deadline": deadline,
        "created_at": datetime.utcnow()
    }
    quiz_id = db.quizAssignments.insert_one(quiz_assignment).inserted_id

    students = db.classMembers.find({"classId": class_id})
    notes_docs = db.notes.find({"_id": {"$in": notes_ids}})
    notes_content = ""

    for note in notes_docs:
        if note["content_type"] == "text":
            notes_content += note["content"] + " "
        elif note["content_type"] == "pdf":
            pdf_file = fs.get(ObjectId(note["content"]))
            notes_content += extract_text(BytesIO(pdf_file.read())) + " "

    for student in students:
        student_id = student["studentId"]
        perf = db.studentPerformance.find_one(
            {"studentId": student_id}) or {"topics": []}
        weak_topics = [t["topic"] for t in perf["topics"] if t.get(
            "total", 0) > 0 and t["correct"] / t["total"] < 0.5]
        prompt = f"Generate questions from: {notes_content}. Focus on: {', '.join(weak_topics)}"
        questions = generate_quiz_questions(prompt)

        personalized_quiz = {
            "quizAssignmentId": quiz_id,
            "studentId": student_id,
            "questions": questions,
            "deadline": deadline,
            "answers": None,
            "score": None,
            "submitted_at": None,
            "feedback": None
        }
        db.personalizedQuizzes.insert_one(personalized_quiz)

    return jsonify({"quiz_assignment_id": str(quiz_id)}), 201


@quizzes_bp.route("/<quiz_id>", methods=["GET"])
@role_required("student")
def get_quiz(quiz_id):
    user_id = get_jwt_identity()
    quiz = db.personalizedQuizzes.find_one(
        {"_id": ObjectId(quiz_id), "studentId": ObjectId(user_id)})

    if not quiz:
        return jsonify({"error": "Quiz not found"}), 404

    questions = [{"question": q["question"], "options": q["options"]}
                 for q in quiz["questions"]]
    return jsonify({"questions": questions, "deadline": quiz["deadline"].isoformat()}), 200


@quizzes_bp.route("/<quiz_id>/submit", methods=["POST"])
@role_required("student")
def submit_quiz(quiz_id):
    user_id = get_jwt_identity()
    quiz = db.personalizedQuizzes.find_one(
        {"_id": ObjectId(quiz_id), "studentId": ObjectId(user_id)})

    if not quiz or quiz["submitted_at"]:
        return jsonify({"error": "Quiz not found or already submitted"}), 400

    answers = request.json["answers"]
    correct_count = sum(1 for i, q in enumerate(
        quiz["questions"]) if q["correct_answer"] == answers[i])
    score = (correct_count / len(quiz["questions"])) * 100

    for i, q in enumerate(quiz["questions"]):
        correct = q["correct_answer"] == answers[i]
        for topic in q["topics"]:
            db.studentPerformance.update_one(
                {"studentId": ObjectId(user_id), "topics.topic": topic},
                {"$inc": {"topics.$.correct": 1 if correct else 0, "topics.$.total": 1}},
                upsert=True
            )

    db.personalizedQuizzes.update_one(
        {"_id": ObjectId(quiz_id)},
        {"$set": {"answers": answers, "score": score, "submitted_at": datetime.utcnow(
        ), "feedback": request.json.get("feedback")}}
    )
    return jsonify({"score": score}), 200


@quizzes_bp.route("/assignments/<quiz_id>/scores", methods=["GET"])
@role_required("teacher")
def get_scores(quiz_id):
    user_id = get_jwt_identity()
    quiz_assignment = db.quizAssignments.find_one({"_id": ObjectId(quiz_id)})

    if not quiz_assignment or str(quiz_assignment["teacherId"]) != user_id:
        return jsonify({"error": "Unauthorized or quiz not found"}), 403

    quizzes = db.personalizedQuizzes.find(
        {"quizAssignmentId": ObjectId(quiz_id)})
    scores = [{"student_id": str(q["studentId"]), "score": q["score"],
               "feedback": q["feedback"]} for q in quizzes if q["score"] is not None]
    return jsonify({"scores": scores}), 200
