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
