from pymongo import MongoClient
from gridfs import GridFS
from dotenv import load_dotenv
import os

load_dotenv()

client = MongoClient(
    os.getenv("MONGO_URI", "mongodb://localhost:27017/"))
db = client["classroom_db"]
fs = GridFS(db)
