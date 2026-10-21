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

def create_user(username: str, password: str, role: str):
    username = username.strip()
    if not username or not password or role not in {"Admin", "Contributor", "Student"}:
        return False
    conn = get_db()
    try:
        pw_hash = hash_password(password)
        conn.execute("INSERT INTO users (username, password_hash, role) VALUES (?, ?, ?)",
                     (username, pw_hash, role))
        conn.commit()
        return True
    except Exception as e:
        print(f"Error creating user: {e}")
        return False
    finally:
        conn.close()


