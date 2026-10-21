from passlib.hash import bcrypt
from database import get_db

def hash_password(password: str) -> str:
    return bcrypt.hash(password)

def verify_password(password: str, hashed: str) -> bool:
    return bcrypt.verify(password, hashed)

def authenticate_user(username: str, password: str):
    conn = get_db()
    user = conn.execute("SELECT * FROM users WHERE username = ?", (username,)).fetchone()
    conn.close()
    
    if user and user["status"] == "Active" and verify_password(password, user["password_hash"]):
        return dict(user)
    return None

