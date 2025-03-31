# GCR-Back

GCR-Back is a backend application for managing classrooms, quizzes, notes, and chat functionalities. It provides APIs for teachers and students to interact with the system.

---

## Table of Contents

- [Features](#features)
- [Technologies Used](#technologies-used)
- [Setup Instructions](#setup-instructions)
- [Environment Variables](#environment-variables)
- [Endpoints](#endpoints)
  - [Authentication](#authentication)
  - [Classes](#classes)
  - [Notes](#notes)
  - [Quizzes](#quizzes)
  - [Chat](#chat)
- [Running the Application](#running-the-application)

---

## Features

- User authentication (teacher and student roles).
- Class creation and management.
- Notes upload and retrieval (text and PDF).
- Quiz generation based on uploaded notes.
- Real-time chat functionality for classes.

---

## Technologies Used

- **Backend Framework**: Flask
- **Database**: MongoDB
- **Authentication**: JWT
- **File Storage**: GridFS
- **Real-time Communication**: Flask-SocketIO
- **AI Integration**: Google Generative AI (Gemini API)

---


## DB DIAGRAM


![diagram-export-3-31-2025-8_52_24-PM](https://github.com/user-attachments/assets/2cd088e1-9b61-484e-b72b-a43f1ce3df8f)


---


## Setup Instructions

1. Clone the repository:

   ```bash
   git clone <repository-url>
   cd gcr-back
   ```

2. Install dependencies:

   ```bash
   pip install -r requirements.txt
   ```

3. Set up the environment variables:

   - Create a `.env` file in the root directory.
   - Add the following variables:
     ```
     GEMINI_API_KEY=<your-gemini-api-key>
     JWT_SECRET_KEY=<your-jwt-secret-key>
     MONGO_URI=mongodb://localhost:27017
     ```

4. Start the MongoDB server:

   ```bash
   mongod
   ```

5. Run the application:

   ```bash
   python backend/app.py
   ```

---

## Environment Variables

| Variable         | Description                        |
| ---------------- | ---------------------------------- |
| `GEMINI_API_KEY` | API key for Google Generative AI.  |
| `JWT_SECRET_KEY` | Secret key for JWT authentication. |
| `MONGO_URI`      | MongoDB connection URI.            |

---

## Endpoints

### Authentication

| Method | Endpoint       | Description                 |
| ------ | -------------- | --------------------------- |
| POST   | `/auth/signup` | Register a new user.        |
| POST   | `/auth/login`  | Log in and get a JWT token. |

### Classes

| Method | Endpoint           | Description                          |
| ------ | ------------------ | ------------------------------------ |
| POST   | `/classes/`        | Create a new class (teacher only).   |
| POST   | `/classes/join`    | Join a class using a code (student). |
| GET    | `/classes/teacher` | Get all classes for a teacher.       |
| GET    | `/classes/student` | Get all classes for a student.       |

### Notes

| Method | Endpoint                    | Description                 |
| ------ | --------------------------- | --------------------------- |
| POST   | `/notes/`                   | Upload notes (text or PDF). |
| GET    | `/notes/class/<class_id>`   | Get all notes for a class.  |
| GET    | `/notes/<note_id>/download` | Download a PDF note.        |

### Quizzes

| Method | Endpoint                                | Description                        |
| ------ | --------------------------------------- | ---------------------------------- |
| POST   | `/quizzes/generate`                     | Generate a quiz (teacher only).    |
| GET    | `/quizzes/<quiz_id>`                    | Get a student's personalized quiz. |
| POST   | `/quizzes/<quiz_id>/submit`             | Submit a quiz (student only).      |
| GET    | `/quizzes/assignments/<quiz_id>/scores` | Get quiz scores (teacher).         |

### Chat

| Method | Endpoint                    | Description                        |
| ------ | --------------------------- | ---------------------------------- |
| POST   | `/chat/messages`            | Post a message in a class chat.    |
| GET    | `/chat/messages/<class_id>` | Get all messages for a class chat. |

---

## Running the Application

1. Ensure MongoDB is running locally.
2. Start the Flask application:
   ```bash
   python backend/app.py
   ```
3. Access the application at `http://127.0.0.1:5000`.

---

## Notes

- Ensure you have the required API keys and environment variables set up before running the application.
- Use tools like Postman or cURL to test the endpoints.
- For real-time chat, use a WebSocket client to connect to the `/chat` namespace.
