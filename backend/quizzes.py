from flask_jwt_extended import get_jwt_identity
from flask import Blueprint, request, jsonify
from bson import ObjectId
from datetime import datetime
from database import db, fs
from auth import role_required
from pdfminer.high_level import extract_text
from io import BytesIO
from question_generator import generate_questions

quizzes_bp = Blueprint("quizzes", __name__)

# Simulated Gemini API integration based on your data format

number_of_questions = 5  # Number of questions to generate per student


def gemini_generate_quiz(pdf_path, n, students, performance_scores):
    quizzes = []
    for student in students:
        quiz_data = generate_questions(
            pdf_path, n, performance_scores[student], student)
        quizzes.append(quiz_data)
    print("quizzes generated!")
    return quizzes


@quizzes_bp.route("/generate", methods=["POST"])
@role_required("teacher")
def generate_quiz():
    """Generate a quiz based on uploaded notes."""
    user_id = get_jwt_identity()  # Assumes JWT is set up elsewhere
    data = request.json
    class_id = ObjectId(data["classId"])
    note_id = ObjectId(data["noteId"])
    deadline = datetime.fromisoformat(data["deadline"])

    # Verify teacher authorization
    if not db.classes.find_one({"_id": class_id, "teacherId": ObjectId(user_id)}):
        return jsonify({"error": "Unauthorized or class not found"}), 403

    # Verify note exists and is a PDF
    note = db.notes.find_one({"_id": note_id})
    if not note or note["content_type"] != "pdf":
        return jsonify({"error": "Note not found or not a PDF"}), 404

    # Retrieve PDF content
    pdf_file = fs.get(ObjectId(note["content"]))
    pdf_path = BytesIO(pdf_file.read())

    # Get students in the class
    students = [str(member["studentId"])
                for member in db.classMembers.find({"classId": class_id})]
    performance_scores = {}
    for student in students:
        perf = db.studentPerformance.find_one({"studentId": ObjectId(student)})
        if perf and perf.get("topics"):
            total_correct = sum(topic["correct"] for topic in perf["topics"])
            total_questions = sum(topic["total"] for topic in perf["topics"])
            performance_scores[student] = total_correct / \
                total_questions if total_questions > 0 else 0
        else:
            performance_scores[student] = 0

    # Generate personalized quizzes using your data format
    quizzes = gemini_generate_quiz(
        pdf_path, number_of_questions, students, performance_scores)

    # Store quiz assignment
    quiz_assignment = {
        "classId": class_id,
        "noteId": note_id,
        "deadline": deadline,
        "created_at": datetime.utcnow()
    }
    quiz_id = db.quizAssignments.insert_one(quiz_assignment).inserted_id

    # Store personalized quizzes for each student
    for quiz_data in quizzes:
        student_id = quiz_data["student_id"]
        questions = quiz_data["questions"]
        personalized_quiz = {
            "quizAssignmentId": quiz_id,
            "studentId": ObjectId(student_id),
            "questions": questions,  # Store full question data including answer and topic
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
    """Retrieve a student's personalized quiz."""
    user_id = get_jwt_identity()
    quiz = db.personalizedQuizzes.find_one(
        {"quizAssignmentId": ObjectId(quiz_id), "studentId": ObjectId(user_id)})
    if not quiz:
        return jsonify({"error": "Quiz not found"}), 404

    # Return only questions and options, hiding answers
    questions = [{"question": q["question"], "options": q["options"]}
                 for q in quiz["questions"]]
    return jsonify({"questions": questions, "deadline": quiz["deadline"].isoformat()}), 200


@quizzes_bp.route("/<quiz_id>/submit", methods=["POST"])
@role_required("student")
def submit_quiz(quiz_id):
    """Submit a quiz and update performance metrics."""
    user_id = get_jwt_identity()
    quiz = db.personalizedQuizzes.find_one(
        {"quizAssignmentId": ObjectId(quiz_id), "studentId": ObjectId(user_id)})

    if not quiz or quiz["submitted_at"]:
        return jsonify({"error": "Quiz not found or already submitted"}), 400

    answers = request.json["answers"]  # List of student answers
    feedback = request.json.get("feedback")
    correct_count = 0
    weak_topics = set()

    # Evaluate answers and identify weak topics
    for i, q in enumerate(quiz["questions"]):
        if q["answer"] == answers[i]:
            correct_count += 1
        else:
            # Add topic of incorrect answer to weak topics
            weak_topics.add(q["topic"])

    score = (correct_count / len(quiz["questions"])) * 100

    db.personalizedQuizzes.update_one(
        {"quizAssignmentId": ObjectId(quiz_id)},
        {"$set": {
            "answers": answers,
            "score": score,
            "submitted_at": datetime.utcnow(),
            "feedback": feedback
        }}
    )

    # Update student performance
    perf = db.studentPerformance.find_one({"studentId": ObjectId(user_id)}) or {
        "topics": [], "weak_topics": []}
    for topic in weak_topics:
        topic_entry = next(
            (t for t in perf["topics"] if t["topic"] == topic), None)
        if topic_entry:
            topic_entry["total"] += 1
            if answers[i] == quiz["questions"][i]["answer"]:
                topic_entry["correct"] += 1
        else:
            perf["topics"].append({"topic": topic, "correct": 0, "total": 1})
        if topic not in perf["weak_topics"]:
            perf["weak_topics"].append(topic)

    total_correct = sum(t["correct"] for t in perf["topics"])
    total_questions = sum(t["total"] for t in perf["topics"])
    performance_matrix = int(
        (total_correct / total_questions) * 100) if total_questions > 0 else 0

    db.studentPerformance.update_one(
        {"studentId": ObjectId(user_id)},
        {"$set": {"topics": perf["topics"], "weak_topics": perf["weak_topics"],
                  "performance_matrix": performance_matrix}},
        upsert=True
    )

    return jsonify({"score": score}), 200


@quizzes_bp.route("/assignments/<quiz_id>/scores", methods=["GET"])
@role_required("teacher")
def get_scores(quiz_id):
    """Retrieve scores and feedback for a quiz assignment."""
    user_id = get_jwt_identity()

    # Fetch the quiz assignment document
    quiz_assignment = db.quizAssignments.find_one({"_id": ObjectId(quiz_id)})
    if not quiz_assignment:
        return jsonify({"error": "Quiz assignment not found"}), 404

    # Fetch the associated class using the classId from the quiz assignment
    class_id = quiz_assignment.get("classId")
    class_doc = db.classes.find_one({"_id": class_id})
    if not class_doc:
        return jsonify({"error": "Associated class not found"}), 404

    # Check if the logged-in teacher is the creator of the class
    teacher_id = str(class_doc.get("teacherId"))
    if teacher_id != user_id:
        return jsonify({"error": "Unauthorized: You do not have permission to view this quiz's scores"}), 403

    # Retrieve scores from personalizedQuizzes collection
    quizzes = db.personalizedQuizzes.find(
        {"quizAssignmentId": ObjectId(quiz_id)})
    scores = []
    for q in quizzes:
        if q.get("score") is not None:  # Check if score exists
            scores.append({
                "student_id": str(q["studentId"]),
                "score": q["score"],
                # Use .get() to safely handle missing feedback
                "feedback": q.get("feedback")
            })

    return jsonify({"scores": scores}), 200
