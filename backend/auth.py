from flask import Blueprint, request, jsonify
from flask_jwt_extended import create_access_token, jwt_required, get_jwt_identity
from werkzeug.security import generate_password_hash, check_password_hash
from bson import ObjectId
from datetime import datetime
from database import db, fs  # Import db and fs from database.py
from functools import wraps

auth_bp = Blueprint("auth", __name__)


@auth_bp.route("/signup", methods=["POST"])
def signup():
    data = request.form
    username = data["username"]
    email = data["email"]
    password = data["password"]
    role = data["role"]

    if role not in ["teacher", "student"]:
        return jsonify({"error": "Invalid role"}), 400

    if db.users.find_one({"$or": [{"username": username}, {"email": email}]}):
        return jsonify({"error": "User already exists"}), 400

    pfp_file = request.files.get("pfp")
    pfp_id = fs.put(pfp_file) if pfp_file else None

    password_hash = generate_password_hash(password)
    user = {
        "username": username,
        "email": email,
        "password_hash": password_hash,
        "role": role,
        "pfp": pfp_id,
        "created_at": datetime.utcnow()
    }
    user_id = db.users.insert_one(user).inserted_id
    token = create_access_token(identity=str(user_id))
    return jsonify({"token": token}), 201


@auth_bp.route("/login", methods=["POST"])
def login():
    data = request.json
    email = data["email"]
    password = data["password"]
    user = db.users.find_one({"email": email})

    if not user or not check_password_hash(user["password_hash"], password):
        return jsonify({"error": "Invalid credentials"}), 401

    token = create_access_token(identity=str(user["_id"]))
    return jsonify({"token": token}), 200


def role_required(role):
    def decorator(f):
        @wraps(f)  # Preserve the original function name
        @jwt_required()
        def wrapper(*args, **kwargs):
            user_id = get_jwt_identity()
            user = db.users.find_one({"_id": ObjectId(user_id)})
            if user["role"] != role:
                return jsonify({"error": "Unauthorized"}), 403
            return f(*args, **kwargs)
        return wrapper
    return decorator
