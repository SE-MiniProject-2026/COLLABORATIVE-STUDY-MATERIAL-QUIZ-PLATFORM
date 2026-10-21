import sqlite3
import os
from passlib.hash import bcrypt

DB_NAME = "csmq.db"
UPLOAD_DIR = "files"
TEST_DIR = "tests"
ADMIN_USERNAME = os.environ.get("CSMQ_ADMIN_USERNAME", "admin")
ADMIN_PASSWORD = os.environ.get("CSMQ_ADMIN_PASSWORD", "admin123")