import sqlite3
import os
from passlib.hash import bcrypt

DB_NAME = "csmq.db"
UPLOAD_DIR = "files"
TEST_DIR = "tests"
ADMIN_USERNAME = os.environ.get("CSMQ_ADMIN_USERNAME", "admin")
ADMIN_PASSWORD = os.environ.get("CSMQ_ADMIN_PASSWORD", "admin123")

def get_db():
    conn = sqlite3.connect(DB_NAME)
    conn.row_factory = sqlite3.Row
    return conn
def init_db():
    if not os.path.exists(UPLOAD_DIR):
        os.makedirs(UPLOAD_DIR)
    if not os.path.exists(TEST_DIR):
        os.makedirs(TEST_DIR)
        
    conn = get_db()
    cursor = conn.cursor()
    
    # Users table
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS users (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            username TEXT UNIQUE NOT NULL,
            password_hash TEXT NOT NULL,
            role TEXT NOT NULL, -- 'Admin', 'Contributor', 'Student'
            status TEXT DEFAULT 'Active' -- 'Active', 'Deactivated'
        )
    ''')
    
    # Study Materials table
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS materials (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            title TEXT NOT NULL,
            subject TEXT NOT NULL,
            description TEXT,
            filename TEXT NOT NULL,
            uploader_id INTEGER,
            FOREIGN KEY(uploader_id) REFERENCES users(id)
        )
    ''')
    
    # Questions table
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS questions (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            question_text TEXT NOT NULL,
            options TEXT NOT NULL, -- comma-separated or JSON list of options
            correct_answer TEXT NOT NULL,
            topic TEXT NOT NULL,
            creator_id INTEGER,
            FOREIGN KEY(creator_id) REFERENCES users(id)
        )
    ''')
    
    # Quizzes table
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS quizzes (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            title TEXT NOT NULL,
            instructions TEXT,
            is_published INTEGER DEFAULT 0,
            creator_id INTEGER,
            FOREIGN KEY(creator_id) REFERENCES users(id)
        )
    ''')
    
    # Quiz Questions Mapping
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS quiz_questions (
            quiz_id INTEGER,
            question_id INTEGER,
            FOREIGN KEY(quiz_id) REFERENCES quizzes(id),
            FOREIGN KEY(question_id) REFERENCES questions(id)
        )
    ''')
    
    # Quiz Attempts and Results
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS attempts (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            student_id INTEGER,
            quiz_id INTEGER,
            score REAL,
            answers TEXT, -- JSON or string mapping
            submission_time TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            FOREIGN KEY(student_id) REFERENCES users(id),
            FOREIGN KEY(quiz_id) REFERENCES quizzes(id)
        )
    ''')
