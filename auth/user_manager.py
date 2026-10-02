"""
MedResearch AI — User management (SQLite + bcrypt).
Handles signup, login, user lookup.
"""

import sqlite3
import bcrypt
from datetime import datetime
from pathlib import Path
from typing import Optional, Dict

DB_PATH = Path(__file__).parent.parent / "users.db"


def init_db():
    """Create users table if it doesn't exist."""
    conn = sqlite3.connect(DB_PATH)
    cursor = conn.cursor()
    cursor.execute("""
        CREATE TABLE IF NOT EXISTS users (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            username TEXT UNIQUE NOT NULL,
            email TEXT UNIQUE NOT NULL,
            password_hash TEXT NOT NULL,
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            last_login TIMESTAMP
        )
    """)
    conn.commit()
    conn.close()


def hash_password(password: str) -> str:
    """Hash a password with bcrypt."""
    salt = bcrypt.gensalt()
    return bcrypt.hashpw(password.encode("utf-8"), salt).decode("utf-8")


def verify_password(password: str, password_hash: str) -> bool:
    """Verify password against hash."""
    try:
        return bcrypt.checkpw(password.encode("utf-8"), password_hash.encode("utf-8"))
    except Exception:
        return False


def create_user(username: str, email: str, password: str) -> Dict:
    """Create a new user. Returns user dict or error."""
    username = username.strip().lower()
    email = email.strip().lower()

    if len(username) < 3:
        return {"success": False, "error": "Username must be at least 3 characters"}
    if len(password) < 6:
        return {"success": False, "error": "Password must be at least 6 characters"}
    if "@" not in email:
        return {"success": False, "error": "Invalid email address"}

    init_db()
    conn = sqlite3.connect(DB_PATH)
    cursor = conn.cursor()

    try:
        password_hash = hash_password(password)
        cursor.execute(
            "INSERT INTO users (username, email, password_hash) VALUES (?, ?, ?)",
            (username, email, password_hash),
        )
        conn.commit()
        user_id = cursor.lastrowid
        conn.close()
        return {
            "success": True,
            "user": {"id": user_id, "username": username, "email": email},
        }
    except sqlite3.IntegrityError as e:
        conn.close()
        if "username" in str(e).lower():
            return {"success": False, "error": "Username already exists"}
        elif "email" in str(e).lower():
            return {"success": False, "error": "Email already registered"}
        return {"success": False, "error": "User already exists"}
    except Exception as e:
        conn.close()
        return {"success": False, "error": f"Error: {str(e)[:100]}"}


def authenticate(username: str, password: str) -> Optional[Dict]:
    """Authenticate user. Returns user dict or None."""
    username = username.strip().lower()
    init_db()
    conn = sqlite3.connect(DB_PATH)
    cursor = conn.cursor()
    cursor.execute(
        "SELECT id, username, email, password_hash FROM users WHERE username = ?",
        (username,),
    )
    row = cursor.fetchone()

    if not row:
        conn.close()
        return None

    user_id, uname, email, password_hash = row

    if verify_password(password, password_hash):
        cursor.execute(
            "UPDATE users SET last_login = ? WHERE id = ?",
            (datetime.now().isoformat(), user_id),
        )
        conn.commit()
        conn.close()
        return {"id": user_id, "username": uname, "email": email}

    conn.close()
    return None


def get_user_count() -> int:
    """Get total number of registered users."""
    init_db()
    conn = sqlite3.connect(DB_PATH)
    cursor = conn.cursor()
    cursor.execute("SELECT COUNT(*) FROM users")
    count = cursor.fetchone()[0]
    conn.close()
    return count