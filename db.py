import sqlite3
from passlib.context import CryptContext
from config import settings

pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto")

def get_db_connection():
    conn = sqlite3.connect(settings.DATABASE_URL, check_same_thread=False)
    conn.row_factory = sqlite3.Row
    return conn

def init_db():
    conn = get_db_connection()
    cur = conn.cursor()
    cur.execute("""
    CREATE TABLE IF NOT EXISTS users(
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        username TEXT UNIQUE NOT NULL,
        password TEXT NOT NULL,
        is_admin INTEGER DEFAULT 0,
        is_active INTEGER DEFAULT 1
    )
    """)
    # إضافة مستخدم افتراضي إذا لم يكن موجوداً (admin/admin)
    admin = cur.execute("SELECT * FROM users WHERE username=?", ("admin",)).fetchone()
    if not admin:
        hashed_pw = pwd_context.hash("admin")
        cur.execute("INSERT INTO users (username, password, is_admin, is_active) VALUES (?, ?, 1, 1)", ("admin", hashed_pw))
    conn.commit()
    conn.close()

def verify_password(plain_password, hashed_password):
    return pwd_context.verify(plain_password, hashed_password)

def get_password_hash(password):
    return pwd_context.hash(password)

def create_user(username, password, is_admin=0):
    conn = get_db_connection()
    cur = conn.cursor()
    hashed_pw = get_password_hash(password)
    try:
        cur.execute("INSERT INTO users (username, password, is_admin, is_active) VALUES (?, ?, ?, 1)", (username, hashed_pw, is_admin))
        conn.commit()
        return True
    except sqlite3.IntegrityError:
        return False
    finally:
        conn.close()

def get_user_by_username(username):
    conn = get_db_connection()
    user = conn.execute("SELECT * FROM users WHERE username=?", (username,)).fetchone()
    conn.close()
    return user

def list_users():
    conn = get_db_connection()
    users = conn.execute("SELECT id, username, is_admin, is_active FROM users").fetchall()
    conn.close()
    return users

def set_active_status(uid, status):
    conn = get_db_connection()
    conn.execute("UPDATE users SET is_active=? WHERE id=?", (status, uid))
    conn.commit()
    conn.close()

# تهيئة قاعدة البيانات عند الاستيراد
init_db()
