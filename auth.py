from flask import Flask, request, jsonify, make_response
from flask_jwt_extended import create_access_token, jwt_required, get_jwt_identity, JWTManager
from flask_bcrypt import Bcrypt
from flask_cors import CORS
from flask_redis import FlaskRedis
from pymongo import MongoClient
import os
from dotenv import load_dotenv
from datetime import timedelta

load_dotenv()

app = Flask(__name__)
app.config["JWT_SECRET_KEY"] = os.getenv("JWT_SECRET")
app.config["REDIS_URL"] = os.getenv("REDIS_URL")
app.config["JWT_ACCESS_TOKEN_EXPIRES"] = timedelta(hours=1)
jwt = JWTManager(app)
bcrypt = Bcrypt(app)
CORS(app, supports_credentials=True)
redis_client = FlaskRedis(app)

# MongoDB setup
client = MongoClient(os.getenv("MONGO_URI"))
db = client.userdb
users_collection = db.users

@app.route('/api/register', methods=['POST'])
def register():
    data = request.get_json()
    
    if not data or not data.get('email') or not data.get('password'):
        return jsonify({'message': 'Missing required fields'}), 400
    
    if users_collection.find_one({'email': data['email']}):
        return jsonify({'message': 'User already exists'}), 409
    
    hashed_password = bcrypt.generate_password_hash(data['password']).decode('utf-8')
    
    new_user = {
        'email': data['email'],
        'password': hashed_password
    }
    
    users_collection.insert_one(new_user)
    
    return jsonify({'message': 'User created successfully'}), 201

@app.route('/api/login', methods=['POST'])
def login():
    data = request.get_json()
    
    if not data or not data.get('email') or not data.get('password'):
        return jsonify({'message': 'Missing required fields'}), 400
    
    user = users_collection.find_one({'email': data['email']})
    
    if not user or not bcrypt.check_password_hash(user['password'], data['password']):
        return jsonify({'message': 'Invalid email or password'}), 401
    
    access_token = create_access_token(identity=str(user['_id']))
    
    return jsonify({
        'message': 'Login successful',
        'access_token': access_token
    }), 200

@app.route('/api/protected', methods=['GET'])
@jwt_required()
def protected():
    current_user_id = get_jwt_identity()
    return jsonify({'message': 'Protected endpoint', 'user_id': current_user_id}), 200

