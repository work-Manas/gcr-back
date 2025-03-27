# fmt: off
from flask import Flask
from flask_jwt_extended import JWTManager
from dotenv import load_dotenv
from extensions import socketio  # Import socketio from extensions.py
from database import db, fs  # Import from the new database module
import os

load_dotenv()

app = Flask(__name__)
app.config["JWT_SECRET_KEY"] = os.getenv("JWT_SECRET_KEY", "your-secret-key")
app.config["JWT_ACCESS_TOKEN_EXPIRES"] = 3600

jwt = JWTManager(app)

# Import blueprints after initializing app and dependencies
from auth import auth_bp
from classes import classes_bp
from notes import notes_bp
from quizzes import quizzes_bp
from chat import chat_bp

app.register_blueprint(auth_bp, url_prefix="/auth")
app.register_blueprint(classes_bp, url_prefix="/classes")
app.register_blueprint(notes_bp, url_prefix="/notes")
app.register_blueprint(quizzes_bp, url_prefix="/quizzes")
app.register_blueprint(chat_bp, url_prefix="/chat")

socketio.init_app(app)

if __name__ == "__main__":
    socketio.run(app, debug=True)