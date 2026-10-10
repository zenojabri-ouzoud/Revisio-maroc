import streamlit as st
import hashlib
import sqlite3
import os
import base64
import random
import time
import json
import math
import re
import shutil
import zipfile
import io
from datetime import datetime, timedelta
from pathlib import Path

# ============================================================
# CONSTANTS
# ============================================================

DB_NAME = "revisiomaroc.db"
UPLOAD_DIR = Path("uploads")
UPLOAD_DIR.mkdir(exist_ok=True)
FILES_DIR = UPLOAD_DIR / "files"
FILES_DIR.mkdir(exist_ok=True)
MODELS_DIR = UPLOAD_DIR / "models"
MODELS_DIR.mkdir(exist_ok=True)
PDF_DIR = UPLOAD_DIR / "pdfs"
PDF_DIR.mkdir(exist_ok=True)
EXERCISES_DIR = UPLOAD_DIR / "exercises"
EXERCISES_DIR.mkdir(exist_ok=True)
IMAGES_DIR = UPLOAD_DIR / "images"
IMAGES_DIR.mkdir(exist_ok=True)

SUBJECTS = {
    "maths": {"name": "الرياضيات", "icon": "📐", "color": "#4A90E2"},
    "french": {"name": "اللغة الفرنسية", "icon": "🇫🇷", "color": "#E74C3C"},
    "english": {"name": "اللغة الإنجليزية", "icon": "🇬🇧", "color": "#3498DB"},
    "history": {"name": "الاجتماعيات", "icon": "🌍", "color": "#F39C12"},
    "islamic": {"name": "التربية الإسلامية", "icon": "🕌", "color": "#27AE60"},
    "pc": {"name": "الفيزياء والكيمياء", "icon": "⚗️", "color": "#9B59B6"},
    "svt": {"name": "علوم الحياة والأرض", "icon": "🧬", "color": "#16A085"},
}

LEVELS = {
    "beginner": "🌱 مبتدئ",
    "intermediate": "🌿 متوسط",
    "advanced": "🌳 متقدم",
}

THEMES = {
    "fcb": {"name": "⚽ FC Barcelona", "bg": "#0A1E3F", "card": "#1A2F5C", "text": "#F0F8FF", "accent": "#A50044", "secondary": "#0F2A52", "border": "#004D98", "highlight": "#00D26A"},
    "real": {"name": "👑 Real Madrid", "bg": "#0F1B2D", "card": "#1E2E4A", "text": "#FFFFFF", "accent": "#FEBE10", "secondary": "#0A1421", "border": "#00529F", "highlight": "#FEBE10"},
    "ahly": {"name": "🦅 الأهلي", "bg": "#1A0A0A", "card": "#2D1515", "text": "#FFF5F5", "accent": "#E30613", "secondary": "#120505", "border": "#8B0000", "highlight": "#FFD700"},
    "moon": {"name": "🌙 Moonlight", "bg": "#0A0E1A", "card": "#1A1F35", "text": "#E8ECFF", "accent": "#7B9FFF", "secondary": "#050810", "border": "#3D4A7A", "highlight": "#FFE57F"},
    "purple": {"name": "🌙 Midnight Purple", "bg": "#0D0B1F", "card": "#1A1735", "text": "#EDE9FE", "accent": "#A78BFA", "secondary": "#221D4A", "border": "#3D3475", "highlight": "#4ADE80"},
    "ocean": {"name": "🌊 Ocean Deep", "bg": "#0A1929", "card": "#132F4C", "text": "#E3F2FD", "accent": "#00B8D4", "secondary": "#0F2537", "border": "#1E4976", "highlight": "#4ADE80"},
    "study": {"name": "📚 Study Mode", "bg": "#1A1410", "card": "#2D2418", "text": "#FFF8E7", "accent": "#D4A574", "secondary": "#0F0B07", "border": "#5C4A2E", "highlight": "#FFD700"},
    "sunset": {"name": "🌅 Golden Sunset", "bg": "#1F1410", "card": "#331F17", "text": "#FFF3E0", "accent": "#FFB74D", "secondary": "#2A1A12", "border": "#5D3A24", "highlight": "#4ADE80"},
    "forest": {"name": "🌿 Forest Emerald", "bg": "#0B1F14", "card": "#143728", "text": "#E8F5E9", "accent": "#4ADE80", "secondary": "#0F2A1D", "border": "#1E5C3D", "highlight": "#00D26A"},
    "light": {"name": "☀️ Light Mode", "bg": "#F5F7FA", "card": "#FFFFFF", "text": "#1A202C", "accent": "#4A90E2", "secondary": "#E2E8F0", "border": "#CBD5E0", "highlight": "#38A169"},
    "galaxy": {"name": "🌌 Galaxy", "bg": "#0D0221", "card": "#1A0533", "text": "#E8D5FF", "accent": "#C77DFF", "secondary": "#050011", "border": "#7209B7", "highlight": "#4CC9F0"},
}

BADGES = {
    "first_quiz": "🎯 أول اختبار", "perfect": "💯 العلامة الكاملة", "5_quizzes": "🔥 مجتهد",
    "10_quizzes": "💪 مثابر", "25_quizzes": "🏃 عدّاء", "50_quizzes": "🚀 صاروخ",
    "100_quizzes": "🌟 أسطورة", "level_5": "⭐ نجم", "level_10": "🌟 نجم لامع",
    "level_20": "👑 ملك", "level_50": "🏆 أسطورة حية", "all_subjects": "🎓 الموسوعي",
    "streak_7": "🔥 أسبوع كامل", "streak_30": "🌋 شهر كامل", "speed_demon": "⚡ البرق",
    "night_owl": "🦉 بومة الليل", "early_bird": "🐦 طائر الصباح", "perfectionist": "✨ المثالي",
    "social_butterfly": "🦋 اجتماعي", "note_master": "📝 سيد الملاحظات", "flashcard_king": "🃏 ملك البطاقات",
    "comeback": "🔄 العودة القوية", "marathon": "🏃 ماراثوني", "weekend_warrior": "⚔️ محارب الأسبوع",
    "book_worm": "📚 قارئ نهم", "downloader": "📥 محمّل", "collector": "🗂️ جامع", "explorer": "🧭 مستكشف",
}

RANKS = [
    (50, "🌟 أسطورة حية"), (35, "🏆 أسطورة"), (20, "👑 خبير"), (12, "🏅 متفوق"),
    (8, "⭐ متميز"), (5, "🎯 مجتهد"), (3, "📖 متعلّم"), (1, "🌱 مبتدئ"),
]

# ============================================================
# DATABASE
# ============================================================

def get_db():
    conn = sqlite3.connect(DB_NAME, check_same_thread=False)
    conn.row_factory = sqlite3.Row
    return conn

def table_columns(cursor, table):
    """Get existing columns of a table"""
    try:
        cursor.execute(f"PRAGMA table_info({table})")
        return [row[1] for row in cursor.fetchall()]
    except Exception:
        return []

def table_exists(cursor, table):
    cursor.execute("SELECT name FROM sqlite_master WHERE type='table' AND name=?", (table,))
    return cursor.fetchone() is not None

def safe_add_column(cursor, table, column, definition):
    """Add a column only if it doesn't exist"""
    cols = table_columns(cursor, table)
    if column not in cols:
        try:
            cursor.execute(f"ALTER TABLE {table} ADD COLUMN {column} {definition}")
            return True
        except Exception as e:
            print(f"Could not add {column} to {table}: {e}")
    return False

def safe_add_column_if_table(cursor, table, column, definition):
    """Add column only if table exists and column doesn't"""
    if table_exists(cursor, table):
        safe_add_column(cursor, table, column, definition)

def migrate_db(cursor):
    """Migrate old DB to new schema by adding missing columns"""
    # lessons: add level, updated_at
    safe_add_column_if_table(cursor, "lessons", "level", "TEXT DEFAULT 'intermediate'")
    safe_add_column_if_table(cursor, "lessons", "updated_at", "TIMESTAMP")
    
    # user_stats: add files_downloaded, files_read
    safe_add_column_if_table(cursor, "user_stats", "files_downloaded", "INTEGER DEFAULT 0")
    safe_add_column_if_table(cursor, "user_stats", "files_read", "INTEGER DEFAULT 0")
    
    # files: add tags, level, is_pinned, reads, updated_at
    safe_add_column_if_table(cursor, "files", "tags", "TEXT DEFAULT ''")
    safe_add_column_if_table(cursor, "files", "level", "TEXT DEFAULT 'intermediate'")
    safe_add_column_if_table(cursor, "files", "is_pinned", "INTEGER DEFAULT 0")
    safe_add_column_if_table(cursor, "files", "reads", "INTEGER DEFAULT 0")
    safe_add_column_if_table(cursor, "files", "updated_at", "TIMESTAMP")

def init_db():
    conn = get_db()
    c = conn.cursor()
    
    # === CREATE TABLES IF NOT EXIST ===
    c.execute("""CREATE TABLE IF NOT EXISTS users (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        username TEXT UNIQUE NOT NULL,
        password_hash TEXT NOT NULL,
        role TEXT DEFAULT 'student',
        full_name TEXT,
        created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
    )""")
    c.execute("""CREATE TABLE IF NOT EXISTS lessons (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        subject TEXT NOT NULL,
        language TEXT DEFAULT 'ar',
        title TEXT NOT NULL,
        content TEXT,
        image_url TEXT,
        pdf_url TEXT,
        owner TEXT,
        level TEXT DEFAULT 'intermediate',
        created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
        updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
    )""")
    c.execute("""CREATE TABLE IF NOT EXISTS questions (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        lesson_id INTEGER NOT NULL,
        question TEXT NOT NULL,
        option_a TEXT NOT NULL,
        option_b TEXT NOT NULL,
        option_c TEXT NOT NULL,
        option_d TEXT NOT NULL,
        correct_answer TEXT NOT NULL,
        explanation TEXT
    )""")
    c.execute("""CREATE TABLE IF NOT EXISTS quiz_history (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        username TEXT NOT NULL,
        lesson_id INTEGER,
        lesson_title TEXT,
        subject TEXT,
        score INTEGER,
        total INTEGER,
        percent REAL,
        created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
    )""")
    c.execute("""CREATE TABLE IF NOT EXISTS favorites (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        username TEXT NOT NULL,
        lesson_id INTEGER NOT NULL,
        UNIQUE(username, lesson_id)
    )""")
    c.execute("""CREATE TABLE IF NOT EXISTS user_stats (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        username TEXT UNIQUE NOT NULL,
        total_points INTEGER DEFAULT 0,
        level INTEGER DEFAULT 1,
        quizzes_taken INTEGER DEFAULT 0,
        perfect_scores INTEGER DEFAULT 0,
        unique_subjects INTEGER DEFAULT 0,
        badges TEXT DEFAULT '[]',
        last_daily TEXT,
        streak INTEGER DEFAULT 0,
        files_downloaded INTEGER DEFAULT 0,
        files_read INTEGER DEFAULT 0
    )""")
    c.execute("""CREATE TABLE IF NOT EXISTS reviews (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        lesson_id INTEGER NOT NULL,
        username TEXT NOT NULL,
        rating INTEGER,
        comment TEXT,
        UNIQUE(lesson_id, username)
    )""")
    c.execute("""CREATE TABLE IF NOT EXISTS messages (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        lesson_id INTEGER NOT NULL,
        username TEXT NOT NULL,
        message TEXT NOT NULL,
        created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
    )""")
    c.execute("""CREATE TABLE IF NOT EXISTS notifications (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        username TEXT NOT NULL,
        title TEXT,
        message TEXT,
        icon TEXT DEFAULT '🔔',
        is_read INTEGER DEFAULT 0,
        created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
    )""")
    c.execute("""CREATE TABLE IF NOT EXISTS flashcards (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        username TEXT NOT NULL,
        subject TEXT,
        front TEXT NOT NULL,
        back TEXT NOT NULL,
        known INTEGER DEFAULT 0
    )""")
    c.execute("""CREATE TABLE IF NOT EXISTS notes (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        username TEXT NOT NULL,
        lesson_id INTEGER NOT NULL,
        note TEXT NOT NULL,
        created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
    )""")
    c.execute("""CREATE TABLE IF NOT EXISTS friends (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        username TEXT NOT NULL,
        friend_username TEXT NOT NULL,
        status TEXT DEFAULT 'pending',
        UNIQUE(username, friend_username)
    )""")
    c.execute("""CREATE TABLE IF NOT EXISTS study_plan (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        username TEXT NOT NULL,
        subject TEXT NOT NULL,
        priority TEXT DEFAULT 'medium',
        target_date TEXT,
        completed INTEGER DEFAULT 0
    )""")
    c.execute("""CREATE TABLE IF NOT EXISTS files (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        subject TEXT,
        category TEXT DEFAULT 'files',
        title TEXT NOT NULL,
        description TEXT,
        file_path TEXT NOT NULL,
        file_name TEXT NOT NULL,
        file_size INTEGER DEFAULT 0,
        file_type TEXT,
        level TEXT DEFAULT 'intermediate',
        tags TEXT DEFAULT '',
        owner TEXT,
        downloads INTEGER DEFAULT 0,
        reads INTEGER DEFAULT 0,
        is_pinned INTEGER DEFAULT 0,
        updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
        created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
    )""")
    c.execute("""CREATE TABLE IF NOT EXISTS lesson_files (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        lesson_id INTEGER NOT NULL,
        file_id INTEGER NOT NULL,
        added_by TEXT,
        is_pinned INTEGER DEFAULT 0,
        display_order INTEGER DEFAULT 0,
        created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
        UNIQUE(lesson_id, file_id)
    )""")
    c.execute("""CREATE TABLE IF NOT EXISTS file_comments (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        file_id INTEGER NOT NULL,
        username TEXT NOT NULL,
        comment TEXT NOT NULL,
        created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
    )""")
    c.execute("""CREATE TABLE IF NOT EXISTS file_ratings (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        file_id INTEGER NOT NULL,
        username TEXT NOT NULL,
        rating INTEGER,
        UNIQUE(file_id, username)
    )""")
    c.execute("""CREATE TABLE IF NOT EXISTS collections (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        title TEXT NOT NULL,
        description TEXT,
        subject TEXT,
        icon TEXT DEFAULT '📦',
        owner TEXT,
        created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
    )""")
    c.execute("""CREATE TABLE IF NOT EXISTS collection_items (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        collection_id INTEGER NOT NULL,
        item_type TEXT NOT NULL,
        item_id INTEGER NOT NULL,
        UNIQUE(collection_id, item_type, item_id)
    )""")
    c.execute("""CREATE TABLE IF NOT EXISTS file_versions (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        file_id INTEGER NOT NULL,
        version INTEGER NOT NULL,
        file_path TEXT NOT NULL,
        file_size INTEGER DEFAULT 0,
        notes TEXT,
        uploaded_by TEXT,
        created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
    )""")
    c.execute("""CREATE TABLE IF NOT EXISTS reading_progress (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        username TEXT NOT NULL,
        file_id INTEGER NOT NULL,
        last_page INTEGER DEFAULT 1,
        total_pages INTEGER DEFAULT 0,
        seconds_spent INTEGER DEFAULT 0,
        updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
        UNIQUE(username, file_id)
    )""")
    c.execute("""CREATE TABLE IF NOT EXISTS download_log (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        username TEXT,
        file_id INTEGER,
        created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
    )""")
    
    # === MIGRATE OLD DB ===
    migrate_db(c)
    
    # === FIX NULL VALUES ===
    try:
        c.execute("UPDATE user_stats SET files_downloaded = 0 WHERE files_downloaded IS NULL")
        c.execute("UPDATE user_stats SET files_read = 0 WHERE files_read IS NULL")
        c.execute("UPDATE lessons SET level = 'intermediate' WHERE level IS NULL")
        c.execute("UPDATE lessons SET updated_at = created_at WHERE updated_at IS NULL")
        c.execute("UPDATE files SET tags = '' WHERE tags IS NULL")
        c.execute("UPDATE files SET level = 'intermediate' WHERE level IS NULL")
        c.execute("UPDATE files SET is_pinned = 0 WHERE is_pinned IS NULL")
        c.execute("UPDATE files SET reads = 0 WHERE reads IS NULL")
        c.execute("UPDATE files SET downloads = 0 WHERE downloads IS NULL")
    except Exception as e:
        print(f"Null fix warning: {e}")
    
    # === DEV USER ===
    dev_hash = hash_password("soufiane2030")
    c.execute("SELECT id FROM users WHERE username = ?", ("soufianeDEV",))
    if not c.fetchone():
        c.execute("INSERT INTO users (username, password_hash, role, full_name) VALUES (?, ?, ?, ?)",
                  ("soufianeDEV", dev_hash, "developer", "Soufiane Ouhazza"))
    
    conn.commit()
    conn.close()

def hash_password(p):
    return hashlib.sha256(p.encode()).hexdigest()

def register_user(u, p, n):
    conn = get_db()
    c = conn.cursor()
    try:
        c.execute("INSERT INTO users (username, password_hash, role, full_name) VALUES (?, ?, ?, ?)",
                  (u, hash_password(p), "student", n))
        c.execute("INSERT INTO user_stats (username) VALUES (?)", (u,))
        conn.commit()
        conn.close()
        return True
    except sqlite3.IntegrityError:
        conn.close()
        return False

def authenticate(u, p):
    conn = get_db()
    c = conn.cursor()
    c.execute("SELECT * FROM users WHERE username = ? AND password_hash = ?", (u, hash_password(p)))
    user = c.fetchone()
    conn.close()
    return user

def row_get(row, key, default=0):
    """Safely get a value from a sqlite Row or dict"""
    try:
        if row is None:
            return default
        if hasattr(row, "keys"):
            if key in row.keys():
                val = row[key]
                return default if val is None else val
            return default
        return row.get(key, default) if isinstance(row, dict) else default
    except Exception:
        return default

def get_user_stats(u):
    conn = get_db()
    c = conn.cursor()
    c.execute("SELECT * FROM user_stats WHERE username = ?", (u,))
    row = c.fetchone()
    if not row:
        c.execute("INSERT INTO user_stats (username) VALUES (?)", (u,))
        conn.commit()
        c.execute("SELECT * FROM user_stats WHERE username = ?", (u,))
        row = c.fetchone()
    conn.close()
    return row

def update_user_stats(u, points=0, quiz=False, perfect=False, subject=None, download=False, read=False):
    conn = get_db()
    c = conn.cursor()
    c.execute("SELECT * FROM user_stats WHERE username = ?", (u,))
    row = c.fetchone()
    if not row:
        c.execute("INSERT INTO user_stats (username) VALUES (?)", (u,))
        conn.commit()
        c.execute("SELECT * FROM user_stats WHERE username = ?", (u,))
        row = c.fetchone()
    
    total_points = (row["total_points"] or 0) + points
    level = total_points // 100 + 1
    quizzes_taken = (row["quizzes_taken"] or 0) + (1 if quiz else 0)
    perfect_scores = (row["perfect_scores"] or 0) + (1 if perfect else 0)
    files_downloaded = (row["files_downloaded"] or 0) + (1 if download else 0)
    files_read = (row["files_read"] or 0) + (1 if read else 0)
    
    subjects = set()
    c.execute("SELECT DISTINCT subject FROM quiz_history WHERE username = ?", (u,))
    for r in c.fetchall():
        if r["subject"]:
            subjects.add(r["subject"])
    if subject:
        subjects.add(subject)
    unique_subjects = len(subjects)
    
    c.execute("""UPDATE user_stats SET total_points=?, level=?, quizzes_taken=?,
                 perfect_scores=?, unique_subjects=?, files_downloaded=?, files_read=? WHERE username=?""",
              (total_points, level, quizzes_taken, perfect_scores, unique_subjects, files_downloaded, files_read, u))
    conn.commit()
    conn.close()
    check_badges(u)

def save_quiz_result(username, lesson_id, lesson_title, subject, score, total, percent):
    conn = get_db()
    c = conn.cursor()
    c.execute("""INSERT INTO quiz_history (username, lesson_id, lesson_title, subject, score, total, percent)
                 VALUES (?, ?, ?, ?, ?, ?, ?)""",
              (username, lesson_id, lesson_title, subject, score, total, percent))
    conn.commit()
    conn.close()

def get_quiz_history(u, limit=20):
    conn = get_db()
    c = conn.cursor()
    c.execute("SELECT * FROM quiz_history WHERE username = ? ORDER BY created_at DESC LIMIT ?", (u, limit))
    rows = c.fetchall()
    conn.close()
    return rows

def get_subject_stats(u):
    conn = get_db()
    c = conn.cursor()
    c.execute("""SELECT subject, COUNT(*) as cnt, AVG(percent) as avg_pct, MAX(percent) as max_pct
                 FROM quiz_history WHERE username = ? GROUP BY subject""", (u,))
    rows = c.fetchall()
    conn.close()
    return rows

def get_weaknesses(u):
    conn = get_db()
    c = conn.cursor()
    c.execute("""SELECT subject, AVG(percent) as avg_pct FROM quiz_history
                 WHERE username = ? GROUP BY subject HAVING avg_pct < 60 ORDER BY avg_pct ASC""", (u,))
    rows = c.fetchall()
    conn.close()
    return rows

def get_leaderboard(period="all"):
    conn = get_db()
    c = conn.cursor()
    if period == "week":
        since = (datetime.now() - timedelta(days=7)).strftime("%Y-%m-%d")
        c.execute("""SELECT u.username, u.full_name, COALESCE(SUM(q.score),0) as pts
                     FROM users u LEFT JOIN quiz_history q ON u.username=q.username
                     WHERE q.created_at >= ? GROUP BY u.username ORDER BY pts DESC LIMIT 50""", (since,))
    elif period == "month":
        since = (datetime.now() - timedelta(days=30)).strftime("%Y-%m-%d")
        c.execute("""SELECT u.username, u.full_name, COALESCE(SUM(q.score),0) as pts
                     FROM users u LEFT JOIN quiz_history q ON u.username=q.username
                     WHERE q.created_at >= ? GROUP BY u.username ORDER BY pts DESC LIMIT 50""", (since,))
    else:
        c.execute("""SELECT u.username, u.full_name, COALESCE(s.total_points,0) as pts
                     FROM users u LEFT JOIN user_stats s ON u.username=s.username
                     ORDER BY pts DESC LIMIT 50""")
    rows = c.fetchall()
    conn.close()
    return rows

def get_weekly_report(u):
    conn = get_db()
    c = conn.cursor()
    since = (datetime.now() - timedelta(days=7)).strftime("%Y-%m-%d")
    c.execute("""SELECT COUNT(*) as cnt, COALESCE(SUM(score),0) as total_score,
                 COALESCE(AVG(percent),0) as avg_pct FROM quiz_history
                 WHERE username = ? AND created_at >= ?""", (u, since))
    row = c.fetchone()
    conn.close()
    return row

def check_badges(u):
    conn = get_db()
    c = conn.cursor()
    c.execute("SELECT * FROM user_stats WHERE username = ?", (u,))
    stats = c.fetchone()
    if not stats:
        conn.close()
        return
    current = json.loads(stats["badges"] or "[]")
    earned = set(current)
    quizzes_taken = stats["quizzes_taken"] or 0
    perfect_scores = stats["perfect_scores"] or 0
    level = stats["level"] or 1
    unique_subjects = stats["unique_subjects"] or 0
    streak = stats["streak"] or 0
    files_downloaded = stats["files_downloaded"] or 0
    files_read = stats["files_read"] or 0
    
    if quizzes_taken >= 1: earned.add("first_quiz")
    if perfect_scores >= 1: earned.add("perfect")
    if quizzes_taken >= 5: earned.add("5_quizzes")
    if quizzes_taken >= 10: earned.add("10_quizzes")
    if quizzes_taken >= 25: earned.add("25_quizzes")
    if quizzes_taken >= 50: earned.add("50_quizzes")
    if quizzes_taken >= 100: earned.add("100_quizzes")
    if level >= 5: earned.add("level_5")
    if level >= 10: earned.add("level_10")
    if level >= 20: earned.add("level_20")
    if level >= 50: earned.add("level_50")
    if unique_subjects >= 7: earned.add("all_subjects")
    if streak >= 7: earned.add("streak_7")
    if streak >= 30: earned.add("streak_30")
    hour = datetime.now().hour
    if 0 <= hour < 5: earned.add("night_owl")
    if 5 <= hour < 7: earned.add("early_bird")
    if files_downloaded >= 10: earned.add("downloader")
    if files_read >= 25: earned.add("book_worm")
    if files_read >= 50: earned.add("collector")
    
    conn2 = get_db()
    c2 = conn2.cursor()
    c2.execute("SELECT COUNT(*) as cnt FROM notes WHERE username = ?", (u,))
    if c2.fetchone()["cnt"] >= 10: earned.add("note_master")
    c2.execute("SELECT COUNT(*) as cnt FROM flashcards WHERE username = ?", (u,))
    if c2.fetchone()["cnt"] >= 20: earned.add("flashcard_king")
    c2.execute("SELECT COUNT(*) as cnt FROM friends WHERE username = ? AND status = 'accepted'", (u,))
    if c2.fetchone()["cnt"] >= 5: earned.add("social_butterfly")
    c2.execute("SELECT COUNT(*) as cnt FROM quiz_history WHERE username = ? AND percent = 100", (u,))
    if c2.fetchone()["cnt"] >= 10: earned.add("perfectionist")
    conn2.close()
    
    new_badges = earned - set(current)
    if new_badges:
        c.execute("UPDATE user_stats SET badges = ? WHERE username = ?", (json.dumps(list(earned)), u))
        for b in new_badges:
            add_notification(u, "شارة جديدة!", BADGES.get(b, b), "🏅")
        conn.commit()
    conn.close()

def get_user_badges(u):
    stats = get_user_stats(u)
    if not stats:
        return []
    return json.loads(stats["badges"] or "[]")

def add_notification(u, title, msg, icon="🔔"):
    conn = get_db()
    c = conn.cursor()
    c.execute("INSERT INTO notifications (username, title, message, icon) VALUES (?, ?, ?, ?)",
              (u, title, msg, icon))
    conn.commit()
    conn.close()

def notify_subject_followers(subject, title, msg, icon="📢"):
    if not subject:
        return
    conn = get_db()
    c = conn.cursor()
    c.execute("SELECT DISTINCT username FROM quiz_history WHERE subject = ?", (subject,))
    users1 = [r["username"] for r in c.fetchall()]
    c.execute("SELECT DISTINCT f.username FROM favorites f JOIN lessons l ON f.lesson_id = l.id WHERE l.subject = ?", (subject,))
    users2 = [r["username"] for r in c.fetchall()]
    conn.close()
    for u in set(users1 + users2):
        add_notification(u, title, msg, icon)

def get_notifications(u, unread=False):
    conn = get_db()
    c = conn.cursor()
    if unread:
        c.execute("SELECT * FROM notifications WHERE username = ? AND is_read = 0 ORDER BY created_at DESC", (u,))
    else:
        c.execute("SELECT * FROM notifications WHERE username = ? ORDER BY created_at DESC LIMIT 50", (u,))
    rows = c.fetchall()
    conn.close()
    return rows

def mark_notifications_read(u):
    conn = get_db()
    c = conn.cursor()
    c.execute("UPDATE notifications SET is_read = 1 WHERE username = ?", (u,))
    conn.commit()
    conn.close()

def check_daily_bonus(u):
    conn = get_db()
    c = conn.cursor()
    c.execute("SELECT last_daily, streak FROM user_stats WHERE username = ?", (u,))
    row = c.fetchone()
    if not row:
        conn.close()
        return 0, 0
    today = datetime.now().strftime("%Y-%m-%d")
    last = row["last_daily"]
    streak = row["streak"] or 0
    if last == today:
        conn.close()
        return 0, streak
    yesterday = (datetime.now() - timedelta(days=1)).strftime("%Y-%m-%d")
    streak = streak + 1 if last == yesterday else 1
    bonus = min(10 + (streak - 1) * 5, 50)
    c.execute("UPDATE user_stats SET last_daily = ?, streak = ? WHERE username = ?", (today, streak, u))
    conn.commit()
    conn.close()
    update_user_stats(u, points=bonus)
    add_notification(u, "🎁 مكافأة يومية", f"حصلت على {bonus} نقطة! سلسلة: {streak} يوم", "🎁")
    return bonus, streak

def get_rank(lvl):
    for threshold, name in RANKS:
        if lvl >= threshold:
            return name
    return "🌱 مبتدئ"

def toggle_favorite(u, lid):
    conn = get_db()
    c = conn.cursor()
    c.execute("SELECT id FROM favorites WHERE username = ? AND lesson_id = ?", (u, lid))
    if c.fetchone():
        c.execute("DELETE FROM favorites WHERE username = ? AND lesson_id = ?", (u, lid))
        result = False
    else:
        c.execute("INSERT INTO favorites (username, lesson_id) VALUES (?, ?)", (u, lid))
        result = True
    conn.commit()
    conn.close()
    return result

def is_favorite(u, lid):
    conn = get_db()
    c = conn.cursor()
    c.execute("SELECT id FROM favorites WHERE username = ? AND lesson_id = ?", (u, lid))
    r = c.fetchone()
    conn.close()
    return r is not None

def get_favorites(u):
    conn = get_db()
    c = conn.cursor()
    c.execute("""SELECT l.* FROM lessons l JOIN favorites f ON l.id = f.lesson_id
                 WHERE f.username = ? ORDER BY f.id DESC""", (u,))
    rows = c.fetchall()
    conn.close()
    return rows

def load_lessons(subject=None, language=None, owner=None, search=None, level=None):
    conn = get_db()
    c = conn.cursor()
    q = "SELECT * FROM lessons WHERE 1=1"
    params = []
    if subject and subject != "all":
        q += " AND subject = ?"
        params.append(subject)
    if language and language != "all":
        q += " AND language = ?"
        params.append(language)
    if level and level != "all":
        q += " AND (level = ? OR level IS NULL)"
        params.append(level)
    if owner:
        q += " AND owner = ?"
        params.append(owner)
    if search:
        q += " AND (title LIKE ? OR content LIKE ?)"
        params.extend([f"%{search}%", f"%{search}%"])
    q += " ORDER BY COALESCE(updated_at, created_at) DESC"
    c.execute(q, params)
    rows = c.fetchall()
    conn.close()
    return rows

def add_lesson(subject, language, title, content, image_url, pdf_url, owner, level="intermediate"):
    conn = get_db()
    c = conn.cursor()
    c.execute("""INSERT INTO lessons (subject, language, title, content, image_url, pdf_url, owner, level, updated_at)
                 VALUES (?, ?, ?, ?, ?, ?, ?, ?, CURRENT_TIMESTAMP)""",
              (subject, language, title, content, image_url, pdf_url, owner, level))
    conn.commit()
    lid = c.lastrowid
    conn.close()
    return lid

def update_lesson(lid, title, content, level):
    conn = get_db()
    c = conn.cursor()
    c.execute("UPDATE lessons SET title=?, content=?, level=?, updated_at=CURRENT_TIMESTAMP WHERE id=?",
              (title, content, level, lid))
    conn.commit()
    conn.close()

def delete_lesson(lid):
    conn = get_db()
    c = conn.cursor()
    c.execute("DELETE FROM questions WHERE lesson_id = ?", (lid,))
    c.execute("DELETE FROM lesson_files WHERE lesson_id = ?", (lid,))
    c.execute("DELETE FROM lessons WHERE id = ?", (lid,))
    conn.commit()
    conn.close()

def load_questions(lid):
    conn = get_db()
    c = conn.cursor()
    c.execute("SELECT * FROM questions WHERE lesson_id = ?", (lid,))
    rows = c.fetchall()
    conn.close()
    return rows

def add_question(lid, question, a, b, c_opt, d, correct, explanation):
    conn = get_db()
    c = conn.cursor()
    c.execute("""INSERT INTO questions (lesson_id, question, option_a, option_b, option_c, option_d, correct_answer, explanation)
                 VALUES (?, ?, ?, ?, ?, ?, ?, ?)""",
              (lid, question, a, b, c_opt, d, correct, explanation))
    conn.commit()
    conn.close()

def delete_question(qid):
    conn = get_db()
    c = conn.cursor()
    c.execute("DELETE FROM questions WHERE id = ?", (qid,))
    conn.commit()
    conn.close()

def upload_file(f, folder="files"):
    if f is None:
        return None
    dest = UPLOAD_DIR / folder
    dest.mkdir(parents=True, exist_ok=True)
    timestamp = int(time.time())
    safe_name = re.sub(r'[^\w\.\-]', '_', f.name)
    path = dest / f"{timestamp}_{safe_name}"
    with open(path, "wb") as out:
        out.write(f.getbuffer())
    return str(path)

def render_pdf(path):
    if not path or not os.path.exists(path):
        st.info("الملف غير متوفر")
        return
    try:
        with open(path, "rb") as f:
            b64 = base64.b64encode(f.read()).decode()
        st.markdown(f'<iframe src="data:application/pdf;base64,{b64}" width="100%" height="700" style="border-radius:12px;border:1px solid #444;"></iframe>', unsafe_allow_html=True)
    except Exception as e:
        st.error(f"تعذر عرض PDF: {e}")

def render_image(path):
    if not path or not os.path.exists(path):
        return
    st.image(path, use_container_width=True)

def add_review(lid, username, rating, comment):
    conn = get_db()
    c = conn.cursor()
    try:
        c.execute("INSERT OR REPLACE INTO reviews (lesson_id, username, rating, comment) VALUES (?, ?, ?, ?)",
                  (lid, username, rating, comment))
        conn.commit()
    except Exception:
        pass
    conn.close()

def get_reviews(lid):
    conn = get_db()
    c = conn.cursor()
    c.execute("SELECT * FROM reviews WHERE lesson_id = ? ORDER BY id DESC", (lid,))
    rows = c.fetchall()
    conn.close()
    return rows

def get_avg_rating(lid):
    conn = get_db()
    c = conn.cursor()
    c.execute("SELECT AVG(rating) as avg FROM reviews WHERE lesson_id = ?", (lid,))
    r = c.fetchone()
    conn.close()
    return r["avg"] if r and r["avg"] else 0

def add_message(lid, username, message):
    conn = get_db()
    c = conn.cursor()
    c.execute("INSERT INTO messages (lesson_id, username, message) VALUES (?, ?, ?)",
              (lid, username, message))
    conn.commit()
    conn.close()

def get_messages(lid):
    conn = get_db()
    c = conn.cursor()
    c.execute("SELECT * FROM messages WHERE lesson_id = ? ORDER BY created_at ASC", (lid,))
    rows = c.fetchall()
    conn.close()
    return rows

def add_flashcard(username, subject, front, back):
    conn = get_db()
    c = conn.cursor()
    c.execute("INSERT INTO flashcards (username, subject, front, back) VALUES (?, ?, ?, ?)",
              (username, subject, front, back))
    conn.commit()
    conn.close()

def get_flashcards(u, s=None):
    conn = get_db()
    c = conn.cursor()
    if s and s != "all":
        c.execute("SELECT * FROM flashcards WHERE username = ? AND subject = ? ORDER BY id DESC", (u, s))
    else:
        c.execute("SELECT * FROM flashcards WHERE username = ? ORDER BY id DESC", (u,))
    rows = c.fetchall()
    conn.close()
    return rows

def delete_flashcard(fid):
    conn = get_db()
    c = conn.cursor()
    c.execute("DELETE FROM flashcards WHERE id = ?", (fid,))
    conn.commit()
    conn.close()

def toggle_flashcard_known(fid):
    conn = get_db()
    c = conn.cursor()
    c.execute("UPDATE flashcards SET known = 1 - known WHERE id = ?", (fid,))
    conn.commit()
    conn.close()

def add_note(username, lesson_id, note):
    conn = get_db()
    c = conn.cursor()
    c.execute("INSERT INTO notes (username, lesson_id, note) VALUES (?, ?, ?)",
              (username, lesson_id, note))
    conn.commit()
    conn.close()

def get_notes(u, lid=None):
    conn = get_db()
    c = conn.cursor()
    if lid:
        c.execute("SELECT * FROM notes WHERE username = ? AND lesson_id = ? ORDER BY created_at DESC", (u, lid))
    else:
        c.execute("SELECT * FROM notes WHERE username = ? ORDER BY created_at DESC", (u,))
    rows = c.fetchall()
    conn.close()
    return rows

def delete_note(nid):
    conn = get_db()
    c = conn.cursor()
    c.execute("DELETE FROM notes WHERE id = ?", (nid,))
    conn.commit()
    conn.close()

def add_friend(u, fu):
    conn = get_db()
    c = conn.cursor()
    try:
        c.execute("INSERT INTO friends (username, friend_username, status) VALUES (?, ?, 'pending')", (u, fu))
        c.execute("INSERT INTO friends (username, friend_username, status) VALUES (?, ?, 'pending')", (fu, u))
        conn.commit()
        conn.close()
        return True
    except sqlite3.IntegrityError:
        conn.close()
        return False

def get_friends(u):
    conn = get_db()
    c = conn.cursor()
    c.execute("SELECT * FROM friends WHERE username = ? ORDER BY status", (u,))
    rows = c.fetchall()
    conn.close()
    return rows

def remove_friend(u, fu):
    conn = get_db()
    c = conn.cursor()
    c.execute("DELETE FROM friends WHERE (username = ? AND friend_username = ?) OR (username = ? AND friend_username = ?)",
              (u, fu, fu, u))
    conn.commit()
    conn.close()

def add_study_plan(username, subject, priority, target_date):
    conn = get_db()
    c = conn.cursor()
    c.execute("INSERT INTO study_plan (username, subject, priority, target_date) VALUES (?, ?, ?, ?)",
              (username, subject, priority, target_date))
    conn.commit()
    conn.close()

def get_study_plan(u):
    conn = get_db()
    c = conn.cursor()
    c.execute("SELECT * FROM study_plan WHERE username = ? ORDER BY completed, target_date", (u,))
    rows = c.fetchall()
    conn.close()
    return rows

def toggle_study_plan(pid):
    conn = get_db()
    c = conn.cursor()
    c.execute("UPDATE study_plan SET completed = 1 - completed WHERE id = ?", (pid,))
    conn.commit()
    conn.close()

def auto_generate_plan(u):
    conn = get_db()
    c = conn.cursor()
    c.execute("DELETE FROM study_plan WHERE username = ? AND completed = 0", (u,))
    weaknesses = get_weaknesses(u)
    for w in weaknesses:
        subject = w["subject"]
        priority = "high" if w["avg_pct"] < 40 else "medium"
        target = (datetime.now() + timedelta(days=7)).strftime("%Y-%m-%d")
        c.execute("INSERT INTO study_plan (username, subject, priority, target_date) VALUES (?, ?, ?, ?)",
                  (u, subject, priority, target))
    for s in SUBJECTS:
        c.execute("SELECT COUNT(*) as cnt FROM study_plan WHERE username = ? AND subject = ?", (u, s))
        if c.fetchone()["cnt"] == 0:
            target = (datetime.now() + timedelta(days=14)).strftime("%Y-%m-%d")
            c.execute("INSERT INTO study_plan (username, subject, priority, target_date) VALUES (?, ?, ?, ?)",
                      (u, s, "low", target))
    conn.commit()
    conn.close()

# ============================================================
# FILES
# ============================================================

def add_file_record(subject, category, title, description, file_path, file_name,
                    file_size, file_type, owner, level="intermediate", tags=""):
    conn = get_db()
    c = conn.cursor()
    c.execute("""INSERT INTO files (subject, category, title, description, file_path, file_name,
                 file_size, file_type, owner, level, tags, updated_at)
                 VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, CURRENT_TIMESTAMP)""",
              (subject, category, title, description, file_path, file_name,
               file_size, file_type, owner, level, tags))
    conn.commit()
    fid = c.lastrowid
    conn.close()
    subj_name = SUBJECTS.get(subject, {"name": subject})["name"] if subject else "عام"
    notify_subject_followers(subject, f"📢 ملف جديد: {title}",
                              f"تم رفع ملف جديد في {subj_name}: {title}", "📂")
    return fid

def get_files(subject=None, category=None, search=None, owner=None, level=None, tag=None, sort="recent"):
    conn = get_db()
    c = conn.cursor()
    q = "SELECT * FROM files WHERE 1=1"
    params = []
    if subject and subject != "all":
        q += " AND subject = ?"
        params.append(subject)
    if category and category != "all":
        q += " AND category = ?"
        params.append(category)
    if level and level != "all":
        q += " AND (level = ? OR level IS NULL)"
        params.append(level)
    if owner:
        q += " AND owner = ?"
        params.append(owner)
    if tag:
        q += " AND COALESCE(tags, '') LIKE ?"
        params.append(f"%{tag}%")
    if search:
        q += " AND (title LIKE ? OR COALESCE(description, '') LIKE ? OR file_name LIKE ? OR COALESCE(tags, '') LIKE ?)"
        params.extend([f"%{search}%"] * 4)
    if sort == "downloads":
        q += " ORDER BY COALESCE(downloads, 0) DESC"
    elif sort == "reads":
        q += " ORDER BY COALESCE(reads, 0) DESC"
    elif sort == "title":
        q += " ORDER BY title ASC"
    else:
        q += " ORDER BY created_at DESC"
    c.execute(q, params)
    rows = c.fetchall()
    conn.close()
    return rows

def get_file(fid):
    conn = get_db()
    c = conn.cursor()
    c.execute("SELECT * FROM files WHERE id = ?", (fid,))
    row = c.fetchone()
    conn.close()
    return row

def delete_file_record(fid):
    conn = get_db()
    c = conn.cursor()
    c.execute("SELECT file_path FROM files WHERE id = ?", (fid,))
    row = c.fetchone()
    if row and row["file_path"]:
        try:
            if os.path.exists(row["file_path"]):
                os.remove(row["file_path"])
        except Exception:
            pass
    c.execute("DELETE FROM lesson_files WHERE file_id = ?", (fid,))
    c.execute("DELETE FROM file_comments WHERE file_id = ?", (fid,))
    c.execute("DELETE FROM file_ratings WHERE file_id = ?", (fid,))
    c.execute("DELETE FROM files WHERE id = ?", (fid,))
    conn.commit()
    conn.close()

def increment_file_download(fid, username=None):
    conn = get_db()
    c = conn.cursor()
    c.execute("UPDATE files SET downloads = COALESCE(downloads, 0) + 1 WHERE id = ?", (fid,))
    c.execute("INSERT INTO download_log (username, file_id) VALUES (?, ?)", (username, fid))
    conn.commit()
    conn.close()
    if username:
        update_user_stats(username, points=2, download=True)

def increment_file_read(fid, username=None):
    conn = get_db()
    c = conn.cursor()
    c.execute("UPDATE files SET reads = COALESCE(reads, 0) + 1 WHERE id = ?", (fid,))
    conn.commit()
    conn.close()
    if username:
        update_user_stats(username, points=1, read=True)

def pin_file(fid):
    conn = get_db()
    c = conn.cursor()
    c.execute("UPDATE files SET is_pinned = 1 - COALESCE(is_pinned, 0) WHERE id = ?", (fid,))
    conn.commit()
    conn.close()

def add_file_comment(file_id, username, comment):
    conn = get_db()
    c = conn.cursor()
    c.execute("INSERT INTO file_comments (file_id, username, comment) VALUES (?, ?, ?)",
              (file_id, username, comment))
    conn.commit()
    conn.close()

def get_file_comments(file_id):
    conn = get_db()
    c = conn.cursor()
    c.execute("SELECT * FROM file_comments WHERE file_id = ? ORDER BY created_at ASC", (file_id,))
    rows = c.fetchall()
    conn.close()
    return rows

def add_file_rating(file_id, username, rating):
    conn = get_db()
    c = conn.cursor()
    c.execute("INSERT OR REPLACE INTO file_ratings (file_id, username, rating) VALUES (?, ?, ?)",
              (file_id, username, rating))
    conn.commit()
    conn.close()

def get_file_avg_rating(file_id):
    conn = get_db()
    c = conn.cursor()
    c.execute("SELECT AVG(rating) as avg, COUNT(*) as cnt FROM file_ratings WHERE file_id = ?", (file_id,))
    r = c.fetchone()
    conn.close()
    return (r["avg"] or 0, r["cnt"] or 0)

def link_file_to_lesson(lesson_id, file_id, added_by, is_pinned=0):
    conn = get_db()
    c = conn.cursor()
    try:
        c.execute("INSERT INTO lesson_files (lesson_id, file_id, added_by, is_pinned) VALUES (?, ?, ?, ?)",
                  (lesson_id, file_id, added_by, is_pinned))
        conn.commit()
        conn.close()
        return True
    except sqlite3.IntegrityError:
        conn.close()
        return False

def unlink_file_from_lesson(lesson_id, file_id):
    conn = get_db()
    c = conn.cursor()
    c.execute("DELETE FROM lesson_files WHERE lesson_id = ? AND file_id = ?", (lesson_id, file_id))
    conn.commit()
    conn.close()

def get_lesson_files(lesson_id, category=None):
    conn = get_db()
    c = conn.cursor()
    if category:
        c.execute("""SELECT f.*, lf.is_pinned as link_pinned FROM files f
                     JOIN lesson_files lf ON f.id = lf.file_id
                     WHERE lf.lesson_id = ? AND f.category = ?
                     ORDER BY lf.is_pinned DESC, COALESCE(f.is_pinned, 0) DESC, f.created_at DESC""",
                  (lesson_id, category))
    else:
        c.execute("""SELECT f.*, lf.is_pinned as link_pinned FROM files f
                     JOIN lesson_files lf ON f.id = lf.file_id
                     WHERE lf.lesson_id = ?
                     ORDER BY lf.is_pinned DESC, COALESCE(f.is_pinned, 0) DESC, f.created_at DESC""",
                  (lesson_id,))
    rows = c.fetchall()
    conn.close()
    return rows

def get_lessons_using_file(file_id):
    conn = get_db()
    c = conn.cursor()
    c.execute("""SELECT l.* FROM lessons l
                 JOIN lesson_files lf ON l.id = lf.lesson_id
                 WHERE lf.file_id = ?""", (file_id,))
    rows = c.fetchall()
    conn.close()
    return rows

def pin_lesson_file(lesson_id, file_id):
    conn = get_db()
    c = conn.cursor()
    c.execute("UPDATE lesson_files SET is_pinned = 1 - COALESCE(is_pinned, 0) WHERE lesson_id = ? AND file_id = ?",
              (lesson_id, file_id))
    conn.commit()
    conn.close()

# ============================================================
# COLLECTIONS
# ============================================================

def add_collection(title, description, subject, icon, owner):
    conn = get_db()
    c = conn.cursor()
    c.execute("""INSERT INTO collections (title, description, subject, icon, owner)
                 VALUES (?, ?, ?, ?, ?)""", (title, description, subject, icon, owner))
    conn.commit()
    cid = c.lastrowid
    conn.close()
    return cid

def get_collections(subject=None):
    conn = get_db()
    c = conn.cursor()
    if subject and subject != "all":
        c.execute("SELECT * FROM collections WHERE subject = ? ORDER BY created_at DESC", (subject,))
    else:
        c.execute("SELECT * FROM collections ORDER BY created_at DESC")
    rows = c.fetchall()
    conn.close()
    return rows

def add_to_collection(collection_id, item_type, item_id):
    conn = get_db()
    c = conn.cursor()
    try:
        c.execute("INSERT INTO collection_items (collection_id, item_type, item_id) VALUES (?, ?, ?)",
                  (collection_id, item_type, item_id))
        conn.commit()
        conn.close()
        return True
    except sqlite3.IntegrityError:
        conn.close()
        return False

def get_collection_items(collection_id):
    conn = get_db()
    c = conn.cursor()
    c.execute("SELECT * FROM collection_items WHERE collection_id = ?", (collection_id,))
    rows = c.fetchall()
    conn.close()
    return rows

def delete_collection(cid):
    conn = get_db()
    c = conn.cursor()
    c.execute("DELETE FROM collection_items WHERE collection_id = ?", (cid,))
    c.execute("DELETE FROM collections WHERE id = ?", (cid,))
    conn.commit()
    conn.close()

def build_collection_zip(collection_id):
    items = get_collection_items(collection_id)
    buf = io.BytesIO()
    with zipfile.ZipFile(buf, "w", zipfile.ZIP_DEFLATED) as zf:
        for it in items:
            if it["item_type"] == "file":
                f = get_file(it["item_id"])
                if f and f["file_path"] and os.path.exists(f["file_path"]):
                    try:
                        zf.write(f["file_path"], arcname=f["file_name"])
                    except Exception:
                        pass
    buf.seek(0)
    return buf.getvalue()

def add_file_version(file_id, version, file_path, file_size, notes, uploaded_by):
    conn = get_db()
    c = conn.cursor()
    c.execute("""INSERT INTO file_versions (file_id, version, file_path, file_size, notes, uploaded_by)
                 VALUES (?, ?, ?, ?, ?, ?)""",
              (file_id, version, file_path, file_size, notes, uploaded_by))
    conn.commit()
    conn.close()

def get_file_versions(file_id):
    conn = get_db()
    c = conn.cursor()
    c.execute("SELECT * FROM file_versions WHERE file_id = ? ORDER BY version DESC", (file_id,))
    rows = c.fetchall()
    conn.close()
    return rows

def get_next_version(file_id):
    conn = get_db()
    c = conn.cursor()
    c.execute("SELECT MAX(version) as v FROM file_versions WHERE file_id = ?", (file_id,))
    r = c.fetchone()
    conn.close()
    return (r["v"] or 0) + 1

def save_reading_progress(username, file_id, last_page, total_pages, seconds):
    conn = get_db()
    c = conn.cursor()
    c.execute("""INSERT INTO reading_progress (username, file_id, last_page, total_pages, seconds_spent, updated_at)
                 VALUES (?, ?, ?, ?, ?, CURRENT_TIMESTAMP)
                 ON CONFLICT(username, file_id) DO UPDATE SET
                 last_page = excluded.last_page,
                 seconds_spent = reading_progress.seconds_spent + excluded.seconds_spent,
                 updated_at = CURRENT_TIMESTAMP""",
              (username, file_id, last_page, total_pages, seconds))
    conn.commit()
    conn.close()

def get_reading_progress(username, file_id):
    conn = get_db()
    c = conn.cursor()
    c.execute("SELECT * FROM reading_progress WHERE username = ? AND file_id = ?", (username, file_id))
    row = c.fetchone()
    conn.close()
    return row

def search_all(query):
    conn = get_db()
    c = conn.cursor()
    like = f"%{query}%"
    results = {"lessons": [], "files": [], "collections": []}
    try:
        c.execute("SELECT * FROM lessons WHERE title LIKE ? OR COALESCE(content, '') LIKE ? LIMIT 20", (like, like))
        results["lessons"] = [dict(r) for r in c.fetchall()]
    except Exception:
        results["lessons"] = []
    try:
        c.execute("""SELECT * FROM files
                     WHERE title LIKE ? OR COALESCE(description, '') LIKE ? OR COALESCE(tags, '') LIKE ? LIMIT 20""",
                  (like, like, like))
        results["files"] = [dict(r) for r in c.fetchall()]
    except Exception:
        results["files"] = []
    try:
        c.execute("SELECT * FROM collections WHERE title LIKE ? OR COALESCE(description, '') LIKE ? LIMIT 10",
                  (like, like))
        results["collections"] = [dict(r) for r in c.fetchall()]
    except Exception:
        results["collections"] = []
    conn.close()
    return results

# ============================================================
# HELPERS
# ============================================================

def format_size(size):
    if not size:
        return "0 B"
    if size < 1024:
        return f"{size} B"
    elif size < 1024 * 1024:
        return f"{size / 1024:.1f} KB"
    elif size < 1024 * 1024 * 1024:
        return f"{size / (1024 * 1024):.1f} MB"
    else:
        return f"{size / (1024 * 1024 * 1024):.2f} GB"

def get_file_icon(file_type, file_name):
    name = (file_name or "").lower()
    ft = (file_type or "").lower()
    if "pdf" in ft or name.endswith(".pdf"): return "📕"
    elif name.endswith((".doc", ".docx")) or "word" in ft: return "📘"
    elif name.endswith((".xls", ".xlsx")) or "excel" in ft: return "📗"
    elif name.endswith((".ppt", ".pptx")) or "powerpoint" in ft: return "📙"
    elif name.endswith((".png", ".jpg", ".jpeg", ".gif", ".bmp", ".webp")) or "image" in ft: return "🖼️"
    elif name.endswith((".mp4", ".avi", ".mov", ".mkv", ".webm")) or "video" in ft: return "🎬"
    elif name.endswith((".mp3", ".wav", ".ogg", ".m4a")) or "audio" in ft: return "🎵"
    elif name.endswith((".zip", ".rar", ".7z", ".tar", ".gz")): return "🗜️"
    elif name.endswith((".py", ".js", ".html", ".css", ".java", ".cpp")): return "💻"
    else: return "📄"

def make_download_button(file_path, file_name, key, label="⬇️ تحميل"):
    if not file_path or not os.path.exists(file_path):
        st.warning("الملف غير موجود")
        return
    try:
        with open(file_path, "rb") as f:
            data = f.read()
        st.download_button(label=label, data=data, file_name=file_name,
                           mime="application/octet-stream", key=key, use_container_width=True)
    except Exception as e:
        st.error(f"خطأ: {e}")

def build_lesson_zip(lesson_id):
    files = get_lesson_files(lesson_id)
    buf = io.BytesIO()
    with zipfile.ZipFile(buf, "w", zipfile.ZIP_DEFLATED) as zf:
        for f in files:
            if f["file_path"] and os.path.exists(f["file_path"]):
                try:
                    zf.write(f["file_path"], arcname=f["file_name"])
                except Exception:
                    pass
    buf.seek(0)
    return buf.getvalue()

def is_arabic_text(text):
    if not text:
        return False
    arabic_pattern = re.compile(r'[\u0600-\u06FF\u0750-\u077F]')
    return bool(arabic_pattern.search(text))

def smart_text(text):
    if not text:
        return
    if is_arabic_text(text):
        st.markdown(f'<div style="direction: rtl; text-align: right;">{text}</div>', unsafe_allow_html=True)
    else:
        st.markdown(f'<div style="direction: ltr; text-align: left;">{text}</div>', unsafe_allow_html=True)

# ============================================================
# THEME
# ============================================================

def apply_theme():
    theme_key = st.session_state.get("theme", "fcb")
    t = THEMES.get(theme_key, THEMES["fcb"])
    css = f"""
    <style>
    @import url('https://fonts.googleapis.com/css2?family=Cairo:wght@400;600;700;900&display=swap');
    * {{ font-family: 'Cairo', sans-serif; }}
    .stApp {{ background-color: {t['bg']}; color: {t['text']}; }}
    .main .block-container {{ padding: 1rem 2rem; max-width: 1200px; }}
    h1, h2, h3, h4, h5, h6 {{ color: {t['text']}; }}
    p, span, div, label {{ color: {t['text']}; }}
    .stButton > button {{
        background: linear-gradient(135deg, {t['accent']}, {t['border']});
        color: #fff; border: 1px solid {t['border']};
        border-radius: 12px; padding: 0.5rem 1.2rem;
        font-weight: 700; transition: all 0.3s;
    }}
    .stButton > button:hover {{ transform: translateY(-2px); box-shadow: 0 8px 20px {t['accent']}66; }}
    .stDownloadButton > button {{
        background: linear-gradient(135deg, {t['highlight']}, {t['accent']});
        color: #000; border: none; border-radius: 12px;
        font-weight: 700; width: 100%;
    }}
    .stTextInput > div > div > input, .stTextArea > div > div > textarea, .stSelectbox > div > div {{
        background-color: {t['card']} !important; color: {t['text']} !important;
        border: 1px solid {t['border']} !important; border-radius: 10px !important;
    }}
    .stTextInput > div > div > input, .stTextArea > div > div > textarea {{
        unicode-bidi: plaintext;
    }}
    .stTabs [data-baseweb="tab"] {{
        background-color: {t['card']}; color: {t['text']};
        border-radius: 10px 10px 0 0; padding: 0.5rem 1rem;
    }}
    .stTabs [aria-selected="true"] {{ background-color: {t['accent']} !important; color: #fff !important; }}
    .card {{
        background-color: {t['card']}; border: 1px solid {t['border']};
        border-radius: 16px; padding: 1.2rem; margin: 0.8rem 0;
        box-shadow: 0 4px 15px rgba(0,0,0,0.3); transition: all 0.3s;
    }}
    .card:hover {{ transform: translateY(-3px); box-shadow: 0 8px 25px {t['accent']}44; }}
    .file-card {{
        background-color: {t['card']}; border: 1px solid {t['border']};
        border-radius: 14px; padding: 1rem; margin: 0.6rem 0;
        transition: all 0.3s;
    }}
    .file-card:hover {{ border-color: {t['accent']}; box-shadow: 0 6px 20px {t['accent']}33; }}
    .file-icon {{ font-size: 2.5rem; display: inline-block; margin-left: 0.5rem; }}
    .file-title {{ font-weight: 700; font-size: 1.1rem; color: {t['text']}; }}
    .file-meta {{ font-size: 0.85rem; opacity: 0.75; color: {t['text']}; }}
    .stat-box {{
        background: linear-gradient(135deg, {t['card']}, {t['secondary']});
        border: 1px solid {t['border']}; border-radius: 14px;
        padding: 1rem; text-align: center; margin: 0.3rem;
    }}
    .stat-number {{ font-size: 2rem; font-weight: 900; color: {t['accent']}; }}
    .badge {{
        display: inline-block; background: {t['secondary']}; border: 1px solid {t['border']};
        border-radius: 20px; padding: 0.3rem 0.8rem; margin: 0.2rem; font-size: 0.9rem;
    }}
    .badge-earned {{ background: linear-gradient(135deg, {t['accent']}, {t['highlight']}); color: #000; font-weight: 700; }}
    .footer {{
        text-align: center; padding: 1.5rem; color: {t['text']};
        opacity: 0.6; font-size: 0.85rem; border-top: 1px solid {t['border']}; margin-top: 2rem;
        direction: ltr;
    }}
    .header-banner {{
        background: linear-gradient(135deg, {t['accent']}, {t['border']});
        border-radius: 16px; padding: 1.5rem; text-align: center; margin-bottom: 1.5rem;
    }}
    .header-banner h1 {{ color: #fff; margin: 0; }}
    .header-banner p {{ color: #fff; opacity: 0.9; margin: 0.3rem 0 0 0; }}
    section[data-testid="stSidebar"] {{ background-color: {t['secondary']} !important; border-left: 1px solid {t['border']}; }}
    .stProgress > div > div > div > div {{ background: linear-gradient(90deg, {t['accent']}, {t['highlight']}); }}
    .stRadio label, .stCheckbox label {{ color: {t['text']} !important; }}
    div[data-testid="stExpander"] {{ background-color: {t['card']}; border: 1px solid {t['border']}; border-radius: 12px; }}
    .rec-card {{ background: {t['card']}; border-right: 4px solid {t['accent']}; border-radius: 12px; padding: 1rem; margin: 0.5rem 0; }}
    .tag-chip {{
        display: inline-block; background: {t['accent']}; color: #fff;
        border-radius: 12px; padding: 0.15rem 0.6rem; font-size: 0.75rem; margin: 0.1rem;
    }}
    .pin-badge {{ background: {t['highlight']}; color: #000; border-radius: 8px; padding: 0.1rem 0.4rem; font-size: 0.7rem; font-weight: 700; }}
    .comment-box {{ background: {t['secondary']}; border-radius: 10px; padding: 0.8rem; margin: 0.4rem 0; }}
    .coll-card {{ background: linear-gradient(135deg, {t['card']}, {t['secondary']}); border: 2px solid {t['accent']}; border-radius: 16px; padding: 1rem; margin: 0.5rem 0; }}
    .mode-reader {{ background: #FAF3E0; color: #2C2C2C; padding: 2rem; border-radius: 12px; line-height: 2; direction: rtl; }}
    .mode-night {{ background: #0F0F1A; color: #C8C8D4; padding: 2rem; border-radius: 12px; line-height: 2; direction: rtl; }}
    </style>
    """
    st.markdown(css, unsafe_allow_html=True)

def footer():
    st.markdown('<div class="footer">© 2026 Soufiane Ouhazza — 3AC RevisioMaroc</div>', unsafe_allow_html=True)

# ============================================================
# AUTH
# ============================================================

def render_auth_home():
    st.markdown("""<div class="header-banner"><h1>📚 3AC RevisioMaroc</h1><p>منصة المراجعة للتلاميذ — السنة الثالثة إعدادي</p></div>""", unsafe_allow_html=True)
    c1, c2, c3 = st.columns(3)
    with c1:
        if st.button("🎓 تلميذ", use_container_width=True):
            st.session_state.auth_page = "student_login"; st.rerun()
    with c2:
        if st.button("🛠️ مطور", use_container_width=True):
            st.session_state.auth_page = "developer_login"; st.rerun()
    with c3:
        if st.button("📝 تسجيل جديد", use_container_width=True):
            st.session_state.auth_page = "register"; st.rerun()
    st.markdown("### ✨ مميزات المنصة")
    cols = st.columns(5)
    feats = [("📝", "اختبارات"), ("📂", "ملفات"), ("📄", "فروض"), ("🃏", "بطاقات"), ("🏆", "نقاط")]
    for i, (ic, name) in enumerate(feats):
        with cols[i]:
            st.markdown(f'<div class="card" style="text-align:center;"><div style="font-size:2rem;">{ic}</div><b>{name}</b></div>', unsafe_allow_html=True)
    footer()

def render_student_login():
    st.markdown('<div class="header-banner"><h1>🎓 دخول التلميذ</h1></div>', unsafe_allow_html=True)
    with st.form("student_login"):
        u = st.text_input("اسم المستخدم")
        p = st.text_input("كلمة المرور", type="password")
        if st.form_submit_button("دخول", use_container_width=True):
            user = authenticate(u, p)
            if user and user["role"] in ("student", "developer"):
                st.session_state.authenticated = True
                st.session_state.username = u
                st.session_state.role = user["role"]
                st.session_state.full_name = user["full_name"]
                st.session_state.page = "dashboard"
                bonus, streak = check_daily_bonus(u)
                if bonus > 0:
                    st.success(f"🎁 مكافأة يومية: +{bonus} نقطة!")
                st.rerun()
            else:
                st.error("خطأ في تسجيل الدخول")
    if st.button("← رجوع"):
        st.session_state.auth_page = "home"; st.rerun()
    footer()

def render_developer_login():
    st.markdown('<div class="header-banner"><h1>🛠️ دخول المطور</h1></div>', unsafe_allow_html=True)
    with st.form("dev_login"):
        u = st.text_input("اسم المستخدم")
        p = st.text_input("كلمة المرور", type="password")
        if st.form_submit_button("دخول", use_container_width=True):
            user = authenticate(u, p)
            if user and user["role"] == "developer":
                st.session_state.authenticated = True
                st.session_state.username = u
                st.session_state.role = "developer"
                st.session_state.full_name = user["full_name"]
                st.session_state.page = "developer_panel"
                st.rerun()
            else:
                st.error("❌ صلاحيات المطور فقط")
    if st.button("← رجوع"):
        st.session_state.auth_page = "home"; st.rerun()
    footer()

def render_register():
    st.markdown('<div class="header-banner"><h1>📝 تسجيل جديد</h1></div>', unsafe_allow_html=True)
    with st.form("register"):
        n = st.text_input("الاسم الكامل")
        u = st.text_input("اسم المستخدم")
        p = st.text_input("كلمة المرور", type="password")
        p2 = st.text_input("تأكيد كلمة المرور", type="password")
        if st.form_submit_button("تسجيل", use_container_width=True):
            if not u or not p or not n:
                st.error("املأ جميع الحقول")
            elif len(p) < 4:
                st.error("كلمة المرور قصيرة")
            elif p != p2:
                st.error("كلمتا المرور غير متطابقتين")
            elif register_user(u, p, n):
                st.success("تم التسجيل ✅")
                st.session_state.auth_page = "student_login"; st.rerun()
            else:
                st.error("اسم المستخدم مستعمل")
    if st.button("← رجوع"):
        st.session_state.auth_page = "home"; st.rerun()
    footer()

def render_auth_page():
    if "auth_page" not in st.session_state:
        st.session_state.auth_page = "home"
    page = st.session_state.auth_page
    if page == "home": render_auth_home()
    elif page == "student_login": render_student_login()
    elif page == "developer_login": render_developer_login()
    elif page == "register": render_register()
    else: render_auth_home()

# ============================================================
# DASHBOARD
# ============================================================

def get_recommendations(u):
    conn = get_db()
    c = conn.cursor()
    recs = []
    c.execute("""SELECT subject, AVG(percent) as avg_pct FROM quiz_history
                 WHERE username = ? GROUP BY subject ORDER BY avg_pct ASC LIMIT 3""", (u,))
    for w in c.fetchall():
        if w["avg_pct"] < 70:
            subj = SUBJECTS.get(w["subject"], {"name": w["subject"], "icon": "📖"})
            recs.append({"type": "weakness", "subject": w["subject"],
                         "title": f"راجع {subj['icon']} {subj['name']}",
                         "desc": f"معدلك {w['avg_pct']:.0f}% — يحتاج تحسين", "icon": "⚠️"})
    c.execute("""SELECT l.* FROM lessons l
                 LEFT JOIN quiz_history q ON l.id = q.lesson_id AND q.username = ?
                 WHERE q.id IS NULL LIMIT 3""", (u,))
    for l in c.fetchall():
        subj = SUBJECTS.get(l["subject"], {"name": l["subject"], "icon": "📖"})
        recs.append({"type": "new", "subject": l["subject"],
                     "title": f"جرب درس: {l['title']}",
                     "desc": f"{subj['icon']} {subj['name']}", "icon": "🆕"})
    conn.close()
    return recs[:5]

def render_dashboard():
    u = st.session_state.username
    stats = get_user_stats(u)
    st.markdown(f'<div class="header-banner"><h1>مرحباً {st.session_state.full_name or u} 👋</h1><p>لنواصل المراجعة!</p></div>', unsafe_allow_html=True)
    level = row_get(stats, "level", 1)
    points = row_get(stats, "total_points", 0)
    quizzes = row_get(stats, "quizzes_taken", 0)
    rank = get_rank(level)
    c1, c2, c3, c4 = st.columns(4)
    with c1: st.markdown(f'<div class="stat-box"><div class="stat-number">{points}</div><div>النقاط</div></div>', unsafe_allow_html=True)
    with c2: st.markdown(f'<div class="stat-box"><div class="stat-number">{level}</div><div>المستوى</div></div>', unsafe_allow_html=True)
    with c3: st.markdown(f'<div class="stat-box"><div class="stat-number">{quizzes}</div><div>الاختبارات</div></div>', unsafe_allow_html=True)
    with c4: st.markdown(f'<div class="stat-box"><div class="stat-number">{rank.split()[0]}</div><div>{rank}</div></div>', unsafe_allow_html=True)
    st.progress((points % 100) / 100, text=f"المستوى {level + 1}: {points % 100}/100")
    st.markdown("### 🔍 بحث ذكي شامل")
    with st.form("smart_search"):
        q = st.text_input("ابحث فـ الدروس، الملفات، الحزم...")
        if st.form_submit_button("🔍 ابحث", use_container_width=True):
            if q.strip():
                st.session_state.search_query = q.strip()
                st.session_state.page = "search_results"
                st.rerun()
    recs = get_recommendations(u)
    if recs:
        st.markdown("### 💡 توصيات ذكية")
        for r in recs:
            st.markdown(f'<div class="rec-card"><b>{r["icon"]} {r["title"]}</b><br><small>{r["desc"]}</small></div>', unsafe_allow_html=True)
    st.markdown("### 📚 المواد")
    cols = st.columns(4)
    for i, (key, subj) in enumerate(SUBJECTS.items()):
        with cols[i % 4]:
            st.markdown(f'<div class="card" style="border-color:{subj["color"]};text-align:center;"><div style="font-size:2.5rem;">{subj["icon"]}</div><div style="font-weight:700;">{subj["name"]}</div></div>', unsafe_allow_html=True)
            if st.button("تصفح", key=f"subj_{key}", use_container_width=True):
                st.session_state.filter_subject = key
                st.session_state.page = "lessons"
                st.rerun()
    st.markdown("### ⚡ إجراءات سريعة")
    c1, c2, c3, c4 = st.columns(4)
    with c1:
        if st.button("🎯 التحدي اليومي", use_container_width=True): st.session_state.page = "daily_challenge"; st.rerun()
    with c2:
        if st.button("⏱️ المراجعة", use_container_width=True): st.session_state.page = "pomodoro"; st.rerun()
    with c3:
        if st.button("📂 كل الملفات", use_container_width=True): st.session_state.page = "files"; st.rerun()
    with c4:
        if st.button("📦 الحزم", use_container_width=True): st.session_state.page = "collections"; st.rerun()
    st.markdown("### 📂 أحدث الملفات")
    recent = get_files()[:5]
    if recent:
        for f in recent:
            subj = SUBJECTS.get(f["subject"], {"name": f["subject"] or "عام", "icon": "📄"})
            icon = get_file_icon(f["file_type"], f["file_name"])
            st.markdown(f'<div class="file-card"><span class="file-icon">{icon}</span><b>{f["title"]}</b> <span class="file-meta">— {subj["icon"]} {subj["name"]} • {format_size(f["file_size"])} • ⬇️ {f["downloads"] or 0}</span></div>', unsafe_allow_html=True)
    else:
        st.info("لا توجد ملفات")
    footer()

# ============================================================
# SEARCH
# ============================================================

def render_search_results():
    st.markdown('<div class="header-banner"><h1>🔍 نتائج البحث</h1></div>', unsafe_allow_html=True)
    query = st.session_state.get("search_query", "")
    if not query:
        st.info("اكتب شيئاً للبحث")
        footer(); return
    st.markdown(f"### نتائج: **{query}**")
    results = search_all(query)
    tabs = st.tabs([f"📖 الدروس ({len(results['lessons'])})", f"📂 الملفات ({len(results['files'])})", f"📦 الحزم ({len(results['collections'])})"])
    with tabs[0]:
        for l in results["lessons"]:
            subj = SUBJECTS.get(l.get("subject", ""), {"name": l.get("subject", ""), "icon": "📖"})
            st.markdown(f"**{subj['icon']} {l['title']}** — {subj['name']}")
            if st.button(f"فتح الدرس", key=f"srch_l_{l['id']}"):
                st.session_state.view_lesson_id = l["id"]
                st.session_state.page = "lesson_view"
                st.rerun()
    with tabs[1]:
        for f in results["files"]:
            icon = get_file_icon(f.get("file_type"), f.get("file_name"))
            st.markdown(f"**{icon} {f['title']}** — {format_size(f.get('file_size', 0))}")
            if st.button(f"عرض الملف", key=f"srch_f_{f['id']}"):
                st.session_state.view_file_id = f["id"]
                st.session_state.page = "file_view"
                st.rerun()
    with tabs[2]:
        for cl in results["collections"]:
            st.markdown(f"**{cl.get('icon', '📦')} {cl['title']}**")
            if st.button(f"عرض الحزمة", key=f"srch_c_{cl['id']}"):
                st.session_state.view_collection_id = cl["id"]
                st.session_state.page = "collection_view"
                st.rerun()
    footer()

# ============================================================
# LESSONS
# ============================================================

def render_lessons():
    st.markdown('<div class="header-banner"><h1>📖 الدروس</h1></div>', unsafe_allow_html=True)
    c1, c2, c3, c4 = st.columns(4)
    with c1:
        subject = st.selectbox("المادة", ["all"] + list(SUBJECTS.keys()),
                               format_func=lambda x: "الكل" if x == "all" else f"{SUBJECTS[x]['icon']} {SUBJECTS[x]['name']}")
    with c2:
        level = st.selectbox("المستوى", ["all"] + list(LEVELS.keys()),
                             format_func=lambda x: "الكل" if x == "all" else LEVELS[x])
    with c3:
        language = st.selectbox("اللغة", ["all", "ar", "fr", "en"],
                                format_func=lambda x: {"all": "الكل", "ar": "العربية", "fr": "الفرنسية", "en": "الإنجليزية"}.get(x, x))
    with c4:
        search = st.text_input("🔍 بحث")
    if "filter_subject" in st.session_state and st.session_state.filter_subject != "all":
        subject = st.session_state.filter_subject
        st.session_state.filter_subject = "all"
    lessons = load_lessons(subject=subject, language=language, search=search, level=level)
    if not lessons:
        st.info("لا توجد دروس")
    for lesson in lessons:
        subj = SUBJECTS.get(lesson["subject"], {"name": lesson["subject"], "icon": "📖"})
        files_count = len(get_lesson_files(lesson["id"]))
        lvl = lesson["level"] if "level" in lesson.keys() and lesson["level"] else "intermediate"
        upd = lesson["updated_at"] if "updated_at" in lesson.keys() and lesson["updated_at"] else lesson["created_at"]
        st.markdown(f"""<div class="card">
            <b style="font-size:1.2rem;">{subj['icon']} {lesson['title']}</b><br>
            <span class="file-meta">{subj['name']} • {LEVELS.get(lvl, 'متوسط')} • {lesson['language'].upper()} • 📎 {files_count} ملف • 📅 {upd[:10] if upd else ''}</span>
        </div>""", unsafe_allow_html=True)
        if st.button("فتح الدرس", key=f"open_lesson_{lesson['id']}", use_container_width=True):
            st.session_state.view_lesson_id = lesson["id"]
            st.session_state.page = "lesson_view"
            st.rerun()
        st.divider()
    footer()

def render_lesson_view():
    lid = st.session_state.get("view_lesson_id")
    if not lid:
        st.error("لم يتم اختيار درس"); footer(); return
    conn = get_db()
    c = conn.cursor()
    c.execute("SELECT * FROM lessons WHERE id = ?", (lid,))
    lesson = c.fetchone()
    conn.close()
    if not lesson:
        st.error("الدرس غير موجود"); footer(); return
    subj = SUBJECTS.get(lesson["subject"], {"name": lesson["subject"], "icon": "📖"})
    fav = is_favorite(st.session_state.username, lid)
    lvl = lesson["level"] if "level" in lesson.keys() and lesson["level"] else "intermediate"
    c1, c2 = st.columns([5, 1])
    with c1:
        st.markdown(f'<div class="header-banner"><h1>{subj["icon"]} {lesson["title"]}</h1><p>{subj["name"]} • {LEVELS.get(lvl, "متوسط")}</p></div>', unsafe_allow_html=True)
    with c2:
        if st.button("❤️" if fav else "🤍", key=f"fav_v_{lid}"):
            toggle_favorite(st.session_state.username, lid); st.rerun()
    if st.button("← العودة للدروس"):
        st.session_state.page = "lessons"; st.rerun()
    tabs = st.tabs(["📖 المحتوى", "📎 الملفات", "📄 نماذج الفروض", "🏋️ التمارين", "🖼️ الصور", "⭐ التقييمات", "💬 المناقشة", "📝 ملاحظاتي"])
    with tabs[0]:
        if lesson["content"]:
            smart_text(lesson["content"])
        if lesson["image_url"]:
            st.image(lesson["image_url"], use_container_width=True)
        if lesson["pdf_url"]:
            render_pdf(lesson["pdf_url"])
        questions = load_questions(lid)
        if questions:
            if st.button(f"🚀 ابدأ الاختبار ({len(questions)} أسئلة)"):
                st.session_state.quiz_lesson_id = lid
                st.session_state.quiz_lesson_title = lesson["title"]
                st.session_state.quiz_subject = lesson["subject"]
                st.session_state.quiz_questions = [dict(q) for q in questions]
                st.session_state.quiz_answers = {}
                st.session_state.quiz_start_time = time.time()
                st.session_state.page = "quiz"
                st.rerun()
        attached = get_lesson_files(lid)
        if attached:
            zip_data = build_lesson_zip(lid)
            if zip_data:
                st.download_button("📦 تحميل كل ملفات الدرس (ZIP)", data=zip_data,
                                   file_name=f"lesson_{lid}_files.zip", mime="application/zip",
                                   key=f"zip_lesson_{lid}")
    with tabs[1]:
        _render_lesson_files_section(lid, "files")
    with tabs[2]:
        _render_lesson_files_section(lid, "models")
    with tabs[3]:
        _render_lesson_files_section(lid, "exercises")
    with tabs[4]:
        _render_lesson_files_section(lid, "images")
    with tabs[5]:
        _render_reviews(lid)
    with tabs[6]:
        _render_discussion(lid)
    with tabs[7]:
        _render_notes(lid)
    footer()

def _render_lesson_files_section(lid, category):
    files = get_lesson_files(lid, category=category)
    is_dev = st.session_state.role == "developer"
    if is_dev:
        with st.expander(f"➕ ربط ملف من المكتبة (النوع: {category})"):
            all_files = [f for f in get_files(category=category) if f["id"] not in [x["id"] for x in files]]
            if all_files:
                with st.form(f"link_form_{lid}_{category}"):
                    opts = {f["id"]: f["title"] for f in all_files}
                    chosen = st.selectbox("اختر ملف", list(opts.keys()), format_func=lambda x: opts[x])
                    pinned = st.checkbox("📌 تثبيت")
                    if st.form_submit_button("🔗 ربط"):
                        link_file_to_lesson(lid, chosen, st.session_state.username, 1 if pinned else 0)
                        st.success("تم الربط"); st.rerun()
            else:
                st.info("لا توجد ملفات متاحة")
    if not files:
        st.info(f"لا توجد ملفات من نوع {category}")
        return
    for f in files:
        icon = get_file_icon(f["file_type"], f["file_name"])
        try:
            pinned = f["link_pinned"] if "link_pinned" in f.keys() else 0
        except Exception:
            pinned = 0
        pin_html = '<span class="pin-badge">📌 مثبت</span>' if pinned or (f["is_pinned"] if "is_pinned" in f.keys() else 0) else ""
        st.markdown(f"""<div class="file-card">
            <span class="file-icon">{icon}</span>
            <b>{f['title']}</b> {pin_html}<br>
            <span class="file-meta">{format_size(f['file_size'])} • 👁️ {f['reads'] or 0} • ⬇️ {f['downloads'] or 0} • 📅 {f['created_at'][:10] if f['created_at'] else ''}</span>
        </div>""", unsafe_allow_html=True)
        c1, c2, c3, c4 = st.columns(4)
        with c1:
            if st.button("📖 قراءة", key=f"read_lf_{lid}_{f['id']}"):
                st.session_state.view_file_id = f["id"]
                st.session_state.page = "file_view"
                st.rerun()
        with c2:
            if st.button("⬇️ تحميل", key=f"dl_lf_{lid}_{f['id']}", use_container_width=True):
                increment_file_download(f["id"], st.session_state.username)
                with open(f["file_path"], "rb") as fh:
                    data = fh.read()
                st.download_button("اضغط", data=data, file_name=f["file_name"],
                                   mime="application/octet-stream", key=f"dl2_{f['id']}")
        with c3:
            if is_dev:
                if st.button("📌", key=f"pin_lf_{lid}_{f['id']}"):
                    pin_lesson_file(lid, f["id"]); st.rerun()
        with c4:
            if is_dev:
                if st.button("🔗 فك الربط", key=f"unlink_{lid}_{f['id']}"):
                    unlink_file_from_lesson(lid, f["id"]); st.rerun()
        st.divider()

def _render_reviews(lid):
    st.markdown("#### ⭐ التقييمات")
    avg = get_avg_rating(lid)
    if avg:
        st.markdown(f"**المتوسط: {avg:.1f}/5**")
    with st.form(f"review_form_{lid}"):
        rating = st.slider("تقييمك", 1, 5, 5)
        comment = st.text_area("تعليقك")
        if st.form_submit_button("إرسال"):
            add_review(lid, st.session_state.username, rating, comment)
            st.rerun()
    for r in get_reviews(lid):
        st.markdown(f"**{r['username']}** — {'⭐' * r['rating']}")
        if r["comment"]:
            smart_text(r["comment"])
        st.divider()

def _render_discussion(lid):
    st.markdown("#### 💬 المناقشة")
    for m in get_messages(lid):
        st.markdown(f"**{m['username']}** _({m['created_at'][:16]})_")
        smart_text(m["message"])
        st.divider()
    with st.form(f"msg_form_{lid}"):
        msg = st.text_area("رسالتك")
        if st.form_submit_button("إرسال"):
            if msg.strip():
                add_message(lid, st.session_state.username, msg.strip()); st.rerun()

def _render_notes(lid):
    st.markdown("#### 📝 ملاحظاتي")
    with st.form(f"note_form_{lid}"):
        note = st.text_area("ملاحظة جديدة")
        if st.form_submit_button("حفظ"):
            if note.strip():
                add_note(st.session_state.username, lid, note.strip()); st.rerun()
    for n in get_notes(st.session_state.username, lid):
        st.markdown(f"_{n['created_at'][:16]}_")
        smart_text(n["note"])
        if st.button("🗑️", key=f"del_note_{n['id']}"):
            delete_note(n["id"]); st.rerun()
        st.divider()

# ============================================================
# FILE VIEW
# ============================================================

def render_file_view():
    fid = st.session_state.get("view_file_id")
    if not fid:
        st.error("لم يتم اختيار ملف"); footer(); return
    f = get_file(fid)
    if not f:
        st.error("الملف غير موجود"); footer(); return
    if st.button("← العودة"):
        st.session_state.page = "files"; st.rerun()
    subj = SUBJECTS.get(f["subject"], {"name": f["subject"] or "عام", "icon": "📄"})
    icon = get_file_icon(f["file_type"], f["file_name"])
    st.markdown(f'<div class="header-banner"><h1>{icon} {f["title"]}</h1><p>{subj["icon"]} {subj["name"]} • {format_size(f["file_size"])}</p></div>', unsafe_allow_html=True)
    st.markdown("### 📖 القراءة")
    mode = st.radio("وضع القراءة", ["عادي", "سبيا (مريح)", "ليلي"], horizontal=True)
    if mode == "سبيا (مريح)":
        st.markdown('<div class="mode-reader">', unsafe_allow_html=True)
    elif mode == "ليلي":
        st.markdown('<div class="mode-night">', unsafe_allow_html=True)
    if f["file_path"] and os.path.exists(f["file_path"]):
        if f["file_name"].lower().endswith(".pdf"):
            read_start = time.time()
            render_pdf(f["file_path"])
            elapsed = int(time.time() - read_start)
            save_reading_progress(st.session_state.username, fid, 1, 0, elapsed)
        elif f["file_name"].lower().endswith((".png", ".jpg", ".jpeg", ".gif", ".webp")):
            render_image(f["file_path"])
        else:
            st.info("لا يمكن قراءة هذا النوع مباشرة")
            increment_file_read(fid, st.session_state.username)
    else:
        st.warning("الملف غير موجود")
    if mode != "عادي":
        st.markdown('</div>', unsafe_allow_html=True)
    st.markdown("### ⭐ تقييم الملف")
    avg, cnt = get_file_avg_rating(fid)
    st.markdown(f"**المعدل:** {avg:.1f}/5 ({cnt} تقييم)")
    with st.form(f"rate_file_{fid}"):
        rating = st.slider("قيّم الملف", 1, 5, 5)
        if st.form_submit_button("إرسال"):
            add_file_rating(fid, st.session_state.username, rating)
            st.rerun()
    st.markdown("### 💬 التعليقات")
    for cm in get_file_comments(fid):
        st.markdown(f'<div class="comment-box"><b>{cm["username"]}</b> _({cm["created_at"][:16]})_<br>{cm["comment"]}</div>', unsafe_allow_html=True)
    with st.form(f"comment_file_{fid}"):
        comment = st.text_area("تعليقك")
        if st.form_submit_button("إرسال"):
            if comment.strip():
                add_file_comment(fid, st.session_state.username, comment.strip()); st.rerun()
    versions = get_file_versions(fid)
    if versions:
        st.markdown("### 🔄 الإصدارات")
        for v in versions:
            st.markdown(f"**v{v['version']}** — {v['notes'] or ''} — {format_size(v['file_size'])} — {v['created_at'][:10]}")
    lessons = get_lessons_using_file(fid)
    if lessons:
        st.markdown("### 🔗 دروس مرتبطة")
        for l in lessons:
            st.markdown(f"- 📖 {l['title']}")
    st.markdown("### ⬇️ التحميل")
    if st.button("📥 تحميل الملف", use_container_width=True):
        increment_file_download(fid, st.session_state.username)
        with open(f["file_path"], "rb") as fh:
            data = fh.read()
        st.download_button("اضغط هنا للتحميل", data=data, file_name=f["file_name"],
                           mime="application/octet-stream", key=f"dl_fileview_{fid}")
    footer()

# ============================================================
# FILES PAGE
# ============================================================

def render_files():
    st.markdown('<div class="header-banner"><h1>📂 كل الملفات</h1></div>', unsafe_allow_html=True)
    tab1, tab2 = st.tabs(["📥 تصفح", "⬆️ رفع"])
    with tab1:
        c1, c2, c3, c4, c5 = st.columns(5)
        with c1:
            subject = st.selectbox("المادة", ["all"] + list(SUBJECTS.keys()),
                                   format_func=lambda x: "الكل" if x == "all" else f"{SUBJECTS[x]['icon']} {SUBJECTS[x]['name']}",
                                   key="files_subject")
        with c2:
            category = st.selectbox("النوع", ["all", "files", "lessons", "exercises", "summaries", "books", "images", "models"],
                                    format_func=lambda x: {"all": "الكل", "files": "ملفات", "lessons": "دروس",
                                                           "exercises": "تمارين", "summaries": "ملخصات", "books": "كتب",
                                                           "images": "صور", "models": "نماذج"}.get(x, x),
                                    key="files_category")
        with c3:
            level = st.selectbox("المستوى", ["all"] + list(LEVELS.keys()),
                                 format_func=lambda x: "الكل" if x == "all" else LEVELS[x],
                                 key="files_level")
        with c4:
            sort = st.selectbox("الترتيب", ["recent", "downloads", "reads", "title"],
                                format_func=lambda x: {"recent": "الأحدث", "downloads": "الأكثر تحميلاً",
                                                       "reads": "الأكثر قراءة", "title": "أبجدي"}[x])
        with c5:
            search = st.text_input("🔍 بحث", key="files_search")
        tag_filter = st.text_input("🏷️ Tag", key="files_tag")
        files_list = get_files(subject=subject, category=category, search=search, level=level,
                               tag=tag_filter if tag_filter else None, sort=sort)
        st.markdown(f"**عدد الملفات:** {len(files_list)}")
        if not files_list:
            st.info("لا توجد ملفات")
        for f in files_list:
            subj = SUBJECTS.get(f["subject"], {"name": f["subject"] or "عام", "icon": "📄"})
            icon = get_file_icon(f["file_type"], f["file_name"])
            tags_val = f["tags"] if "tags" in f.keys() and f["tags"] else ""
            tags_html = "".join([f'<span class="tag-chip">{t.strip()}</span>' for t in tags_val.split(",") if t.strip()])
            pin = '<span class="pin-badge">📌</span>' if (f["is_pinned"] if "is_pinned" in f.keys() else 0) else ""
            st.markdown(f"""<div class="file-card">
                <span class="file-icon">{icon}</span>
                <b>{f['title']}</b> {pin}<br>
                <span class="file-meta">{subj['icon']} {subj['name']} • {format_size(f['file_size'])} • 👁️ {f['reads'] or 0} • ⬇️ {f['downloads'] or 0}</span>
                {tags_html}
            </div>""", unsafe_allow_html=True)
            c1, c2, c3 = st.columns(3)
            with c1:
                if st.button("📖 قراءة", key=f"read_f_{f['id']}"):
                    st.session_state.view_file_id = f["id"]
                    st.session_state.page = "file_view"
                    st.rerun()
            with c2:
                if st.button("⬇️ تحميل", key=f"dl_f_{f['id']}"):
                    increment_file_download(f["id"], st.session_state.username)
                    with open(f["file_path"], "rb") as fh:
                        data = fh.read()
                    st.download_button("اضغط", data=data, file_name=f["file_name"],
                                       mime="application/octet-stream", key=f"dlbtn_{f['id']}")
            with c3:
                if st.button("🔗 دروس", key=f"lessons_f_{f['id']}"):
                    ls = get_lessons_using_file(f["id"])
                    if ls:
                        for l in ls: st.write(f"- {l['title']}")
                    else:
                        st.warning("غير مرتبط")
            st.divider()
    with tab2:
        with st.form("upload_new_file"):
            title = st.text_input("عنوان الملف *")
            subject = st.selectbox("المادة", list(SUBJECTS.keys()),
                                   format_func=lambda x: f"{SUBJECTS[x]['icon']} {SUBJECTS[x]['name']}",
                                   key="up_subj")
            category = st.selectbox("النوع", ["files", "lessons", "exercises", "summaries", "books", "images", "models"],
                                    format_func=lambda x: {"files": "ملف", "lessons": "درس", "exercises": "تمارين",
                                                           "summaries": "ملخص", "books": "كتاب", "images": "صور",
                                                           "models": "نموذج"}.get(x, x))
            level = st.selectbox("المستوى", list(LEVELS.keys()), format_func=lambda x: LEVELS[x])
            description = st.text_area("الوصف")
            tags = st.text_input("Tags")
            uploaded = st.file_uploader("اختر الملف *")
            if st.form_submit_button("⬆️ رفع", use_container_width=True):
                if not title or not uploaded:
                    st.error("املأ الحقول المطلوبة")
                else:
                    path = upload_file(uploaded, "files")
                    size = os.path.getsize(path) if path else 0
                    add_file_record(subject, category, title, description, path, uploaded.name,
                                    size, uploaded.type or "", st.session_state.username, level, tags)
                    st.success("تم الرفع ✅"); st.rerun()
    footer()

# ============================================================
# COLLECTIONS
# ============================================================

def render_collections():
    st.markdown('<div class="header-banner"><h1>📦 الحزم</h1></div>', unsafe_allow_html=True)
    tab1, tab2 = st.tabs(["📥 تصفح", "➕ إنشاء"])
    with tab1:
        subject = st.selectbox("المادة", ["all"] + list(SUBJECTS.keys()),
                               format_func=lambda x: "الكل" if x == "all" else f"{SUBJECTS[x]['icon']} {SUBJECTS[x]['name']}",
                               key="coll_subject")
        colls = get_collections(subject)
        if not colls:
            st.info("لا توجد حزم")
        for cl in colls:
            items = get_collection_items(cl["id"])
            st.markdown(f"""<div class="coll-card">
                <h3>{cl['icon']} {cl['title']}</h3>
                <p>{cl['description'] or ''}</p>
                <span class="file-meta">📦 {len(items)} عنصر • 👤 {cl['owner']}</span>
            </div>""", unsafe_allow_html=True)
            c1, c2, c3 = st.columns(3)
            with c1:
                if st.button("👁️ عرض", key=f"view_coll_{cl['id']}"):
                    st.session_state.view_collection_id = cl["id"]
                    st.session_state.page = "collection_view"
                    st.rerun()
            with c2:
                zip_data = build_collection_zip(cl["id"])
                if zip_data:
                    st.download_button("📦 تحميل", data=zip_data,
                                       file_name=f"collection_{cl['id']}.zip",
                                       mime="application/zip", key=f"zip_coll_{cl['id']}")
            with c3:
                if st.session_state.role == "developer":
                    if st.button("🗑️ حذف", key=f"del_coll_{cl['id']}"):
                        delete_collection(cl["id"]); st.rerun()
            st.divider()
    with tab2:
        if st.session_state.role != "developer":
            st.warning("فقط المطور")
        else:
            with st.form("create_coll"):
                title = st.text_input("العنوان *")
                description = st.text_area("الوصف")
                subject = st.selectbox("المادة", list(SUBJECTS.keys()),
                                       format_func=lambda x: f"{SUBJECTS[x]['icon']} {SUBJECTS[x]['name']}",
                                       key="new_coll_subj")
                icon = st.text_input("الأيقونة", value="📦")
                if st.form_submit_button("إنشاء"):
                    if title:
                        add_collection(title, description, subject, icon, st.session_state.username)
                        st.success("تم"); st.rerun()
    footer()

def render_collection_view():
    cid = st.session_state.get("view_collection_id")
    if not cid:
        st.error("لم يتم اختيار حزمة"); footer(); return
    conn = get_db()
    c = conn.cursor()
    c.execute("SELECT * FROM collections WHERE id = ?", (cid,))
    coll = c.fetchone()
    conn.close()
    if not coll:
        st.error("غير موجودة"); footer(); return
    st.markdown(f'<div class="header-banner"><h1>{coll["icon"]} {coll["title"]}</h1><p>{coll["description"] or ""}</p></div>', unsafe_allow_html=True)
    if st.button("← العودة"):
        st.session_state.page = "collections"; st.rerun()
    items = get_collection_items(cid)
    st.markdown(f"### 📦 {len(items)} عنصر")
    for it in items:
        if it["item_type"] == "file":
            f = get_file(it["item_id"])
            if f:
                icon = get_file_icon(f["file_type"], f["file_name"])
                st.markdown(f"- {icon} **{f['title']}** — {format_size(f['file_size'])}")
        elif it["item_type"] == "lesson":
            conn = get_db()
            c = conn.cursor()
            c.execute("SELECT * FROM lessons WHERE id = ?", (it["item_id"],))
            l = c.fetchone()
            conn.close()
            if l:
                st.markdown(f"- 📖 **{l['title']}**")
    zip_data = build_collection_zip(cid)
    if zip_data:
        st.download_button("📦 تحميل الحزمة كاملة", data=zip_data,
                           file_name=f"{coll['title']}.zip", mime="application/zip")
    if st.session_state.role == "developer":
        st.markdown("### ➕ إضافة عنصر")
        with st.form("add_coll_item"):
            item_type = st.selectbox("النوع", ["file", "lesson"])
            if item_type == "file":
                files = get_files()
                opts = {f["id"]: f["title"] for f in files}
                chosen = st.selectbox("اختر", list(opts.keys()), format_func=lambda x: opts[x])
            else:
                lessons = load_lessons()
                opts = {l["id"]: l["title"] for l in lessons}
                chosen = st.selectbox("اختر", list(opts.keys()), format_func=lambda x: opts[x])
            if st.form_submit_button("إضافة"):
                add_to_collection(cid, item_type, chosen)
                st.success("تم"); st.rerun()
    footer()

# ============================================================
# QUIZ
# ============================================================

def _render_quiz_ui(questions, lesson_id):
    total = len(questions)
    start = st.session_state.get("quiz_start_time", time.time())
    remaining = max(0, 600 - (time.time() - start))
    if remaining <= 0:
        st.error("⏰ انتهى الوقت!")
        if st.button("عرض النتيجة"):
            st.session_state.page = "dashboard"; st.rerun()
        return
    mins, secs = divmod(int(remaining), 60)
    st.markdown(f"### ⏱️ الوقت المتبقي: {mins:02d}:{secs:02d}")
    st.progress(remaining / 600)
    answers = st.session_state.get("quiz_answers", {})
    if "quiz_current" not in st.session_state:
        st.session_state.quiz_current = 0
    idx = st.session_state.quiz_current
    if idx >= total:
        score = sum(1 for i, q in enumerate(questions) if answers.get(i) == q["correct_answer"])
        percent = (score / total) * 100 if total else 0
        save_quiz_result(st.session_state.username, lesson_id,
                         st.session_state.quiz_lesson_title, st.session_state.quiz_subject,
                         score, total, percent)
        update_user_stats(st.session_state.username, points=score * 10, quiz=True,
                          perfect=(score == total), subject=st.session_state.quiz_subject)
        st.success(f"🎉 نتيجتك: {score}/{total} ({percent:.1f}%)")
        if score == total: st.balloons()
        st.markdown("### 📋 التصحيح")
        for i, q in enumerate(questions):
            ua = answers.get(i); ca = q["correct_answer"]
            st.markdown(f"{'✅' if ua == ca else '❌'} **{q['question']}**")
            st.write(f"إجابتك: {ua.upper() if ua else '—'} | الصحيحة: {ca.upper()}")
            if q.get("explanation"):
                smart_text(q["explanation"])
            st.divider()
        if st.button("العودة"):
            for k in ["quiz_questions", "quiz_answers", "quiz_current", "quiz_start_time"]:
                st.session_state.pop(k, None)
            st.session_state.page = "dashboard"; st.rerun()
        return
    q = questions[idx]
    st.markdown(f"#### السؤال {idx + 1} / {total}")
    smart_text(q["question"])
    opts = {"a": q["option_a"], "b": q["option_b"], "c": q["option_c"], "d": q["option_d"]}
    sel = st.radio("اختر:", list(opts.keys()), format_func=lambda x: f"{x.upper()}) {opts[x]}",
                   index=None, key=f"q_{idx}")
    c1, c2 = st.columns(2)
    with c1:
        if st.button("السابق", disabled=(idx == 0)):
            st.session_state.quiz_current -= 1; st.rerun()
    with c2:
        if st.button("التالي", disabled=(sel is None)):
            answers[idx] = sel
            st.session_state.quiz_answers = answers
            st.session_state.quiz_current += 1
            st.rerun()

def render_quiz():
    st.markdown('<div class="header-banner"><h1>📝 الاختبار</h1></div>', unsafe_allow_html=True)
    questions = st.session_state.get("quiz_questions", [])
    lid = st.session_state.get("quiz_lesson_id")
    if not questions:
        st.warning("لا توجد أسئلة")
        if st.button("رجوع"): st.session_state.page = "lessons"; st.rerun()
        return
    _render_quiz_ui(questions, lid)
    footer()

def render_quick_review():
    st.markdown('<div class="header-banner"><h1>⚡ مراجعة سريعة</h1></div>', unsafe_allow_html=True)
    subject = st.selectbox("المادة", list(SUBJECTS.keys()),
                           format_func=lambda x: f"{SUBJECTS[x]['icon']} {SUBJECTS[x]['name']}")
    conn = get_db()
    c = conn.cursor()
    c.execute("""SELECT q.* FROM questions q JOIN lessons l ON q.lesson_id = l.id
                 WHERE l.subject = ? ORDER BY RANDOM() LIMIT 10""", (subject,))
    questions = [dict(r) for r in c.fetchall()]
    conn.close()
    if not questions:
        st.info("لا توجد أسئلة"); footer(); return
    if "qr_answers" not in st.session_state or st.session_state.get("qr_subject") != subject:
        st.session_state.qr_answers = {}; st.session_state.qr_subject = subject
    answers = st.session_state.qr_answers
    for i, q in enumerate(questions):
        st.markdown(f"**{i+1}. {q['question']}**")
        opts = {"a": q["option_a"], "b": q["option_b"], "c": q["option_c"], "d": q["option_d"]}
        ch = st.radio("", list(opts.keys()), format_func=lambda x: f"{x.upper()}) {opts[x]}",
                      index=None, key=f"qr_{i}")
        if ch: answers[i] = ch
        st.divider()
    if st.button("✅ تصحيح"):
        score = sum(1 for i, q in enumerate(questions) if answers.get(i) == q["correct_answer"])
        st.success(f"نتيجتك: {score}/{len(questions)}")
    footer()

# ============================================================
# DAILY
# ============================================================

def get_daily_challenge():
    conn = get_db()
    c = conn.cursor()
    c.execute("SELECT * FROM questions ORDER BY RANDOM() LIMIT 5")
    rows = c.fetchall()
    conn.close()
    return [dict(r) for r in rows]

def save_daily_challenge(u, score, total):
    conn = get_db()
    c = conn.cursor()
    c.execute("""INSERT INTO quiz_history (username, lesson_id, lesson_title, subject, score, total, percent)
                 VALUES (?, ?, ?, ?, ?, ?, ?)""",
              (u, -1, "التحدي اليومي", "daily", score, total, (score/total)*100 if total else 0))
    conn.commit(); conn.close()
    update_user_stats(u, points=score * 15, quiz=True, perfect=(score == total), subject="daily")

def render_daily_challenge():
    st.markdown('<div class="header-banner"><h1>🎯 التحدي اليومي</h1></div>', unsafe_allow_html=True)
    st.write("5 أسئلة عشوائية — 15 نقطة لكل إجابة صحيحة!")
    if "daily_questions" not in st.session_state:
        st.session_state.daily_questions = get_daily_challenge()
        st.session_state.daily_answers = {}
        st.session_state.daily_done = False
    questions = st.session_state.daily_questions
    if not questions:
        st.warning("لا أسئلة"); footer(); return
    if st.session_state.daily_done:
        score = sum(1 for i, q in enumerate(questions) if st.session_state.daily_answers.get(i) == q["correct_answer"])
        st.success(f"🎉 نتيجتك: {score}/{len(questions)}")
        if score == len(questions): st.balloons()
        for i, q in enumerate(questions):
            ua = st.session_state.daily_answers.get(i); ca = q["correct_answer"]
            st.markdown(f"{'✅' if ua == ca else '❌'} {q['question']} — الصحيحة: {ca.upper()}")
        if st.button("تحدي جديد"):
            st.session_state.daily_questions = get_daily_challenge()
            st.session_state.daily_answers = {}
            st.session_state.daily_done = False
            st.rerun()
        footer(); return
    for i, q in enumerate(questions):
        st.markdown(f"**{i+1}. {q['question']}**")
        opts = {"a": q["option_a"], "b": q["option_b"], "c": q["option_c"], "d": q["option_d"]}
        ch = st.radio("", list(opts.keys()), format_func=lambda x: f"{x.upper()}) {opts[x]}",
                      index=None, key=f"daily_{i}")
        if ch: st.session_state.daily_answers[i] = ch
    if st.button("✅ إرسال"):
        score = sum(1 for i, q in enumerate(questions) if st.session_state.daily_answers.get(i) == q["correct_answer"])
        save_daily_challenge(st.session_state.username, score, len(questions))
        st.session_state.daily_done = True
        st.rerun()
    footer()

# ============================================================
# POMODORO
# ============================================================

def render_pomodoro_page():
    st.markdown('<div class="header-banner"><h1>⏱️ مؤقت المراجعة</h1></div>', unsafe_allow_html=True)
    st.write("25 دقيقة مراجعة + 5 دقائق راحة")
    if "pomodoro_start" not in st.session_state:
        st.session_state.pomodoro_start = None
        st.session_state.pomodoro_duration = 25 * 60
        st.session_state.pomodoro_mode = "work"
    c1, c2, c3 = st.columns(3)
    with c1:
        if st.button("▶️ ابدأ 25 دقيقة"):
            st.session_state.pomodoro_start = time.time()
            st.session_state.pomodoro_duration = 25 * 60
            st.session_state.pomodoro_mode = "work"; st.rerun()
    with c2:
        if st.button("☕ راحة 5 دقائق"):
            st.session_state.pomodoro_start = time.time()
            st.session_state.pomodoro_duration = 5 * 60
            st.session_state.pomodoro_mode = "break"; st.rerun()
    with c3:
        if st.button("⏹️ إيقاف"):
            st.session_state.pomodoro_start = None; st.rerun()
    if st.session_state.pomodoro_start:
        remaining = max(0, st.session_state.pomodoro_duration - (time.time() - st.session_state.pomodoro_start))
        mins, secs = divmod(int(remaining), 60)
        mode = "🔴 مراجعة" if st.session_state.pomodoro_mode == "work" else "🟢 راحة"
        st.markdown(f"<h1 style='text-align:center;font-size:4rem;'>{mins:02d}:{secs:02d}</h1>", unsafe_allow_html=True)
        st.markdown(f"<p style='text-align:center;'>{mode}</p>", unsafe_allow_html=True)
        st.progress(1 - (remaining / st.session_state.pomodoro_duration))
        if remaining <= 0:
            st.success("انتهى الوقت!"); st.balloons()
            st.session_state.pomodoro_start = None
    footer()

# ============================================================
# FLASHCARDS
# ============================================================

def render_flashcards():
    st.markdown('<div class="header-banner"><h1>🃏 البطاقات التعليمية</h1></div>', unsafe_allow_html=True)
    with st.expander("➕ إضافة بطاقة"):
        with st.form("add_fc"):
            subject = st.selectbox("المادة", list(SUBJECTS.keys()),
                                   format_func=lambda x: f"{SUBJECTS[x]['icon']} {SUBJECTS[x]['name']}")
            front = st.text_input("الوجه"); back = st.text_area("الظهر")
            if st.form_submit_button("إضافة"):
                if front and back:
                    add_flashcard(st.session_state.username, subject, front, back); st.rerun()
    sf = st.selectbox("تصفية", ["all"] + list(SUBJECTS.keys()),
                      format_func=lambda x: "الكل" if x == "all" else SUBJECTS[x]["name"])
    cards = get_flashcards(st.session_state.username, sf)
    if not cards: st.info("لا توجد بطاقات")
    for c in cards:
        s = "✅" if c["known"] else "❌"
        with st.expander(f"{s} {c['front']}"):
            smart_text(c["back"])
            c1, c2 = st.columns(2)
            with c1:
                if st.button("🔄", key=f"t_{c['id']}"):
                    toggle_flashcard_known(c["id"]); st.rerun()
            with c2:
                if st.button("🗑️", key=f"d_{c['id']}"):
                    delete_flashcard(c["id"]); st.rerun()
    footer()

# ============================================================
# STUDY PLAN
# ============================================================

def render_study_plan():
    st.markdown('<div class="header-banner"><h1>📅 خطة الدراسة</h1></div>', unsafe_allow_html=True)
    c1, c2 = st.columns(2)
    with c1:
        if st.button("🔄 توليد تلقائي", use_container_width=True):
            auto_generate_plan(st.session_state.username); st.success("تم"); st.rerun()
    with c2:
        with st.expander("➕ إضافة مهمة"):
            with st.form("add_plan"):
                subject = st.selectbox("المادة", list(SUBJECTS.keys()),
                                       format_func=lambda x: SUBJECTS[x]["name"])
                priority = st.selectbox("الأولوية", ["high", "medium", "low"],
                                        format_func=lambda x: {"high": "🔴 عالية", "medium": "🟡 متوسطة", "low": "🟢 منخفضة"}[x])
                target = st.date_input("التاريخ")
                if st.form_submit_button("إضافة"):
                    add_study_plan(st.session_state.username, subject, priority, target.strftime("%Y-%m-%d")); st.rerun()
    plan = get_study_plan(st.session_state.username)
    if not plan: st.info("لا توجد خطة")
    for p in plan:
        s = "✅" if p["completed"] else "⏳"
        subj_name = SUBJECTS.get(p["subject"], {"name": p["subject"]})["name"]
        st.markdown(f"{s} **{subj_name}** — {p['priority']} — {p['target_date'] or ''}")
        if st.button("تبديل", key=f"t_plan_{p['id']}"):
            toggle_study_plan(p["id"]); st.rerun()
    footer()

# ============================================================
# FRIENDS
# ============================================================

def render_friends():
    st.markdown('<div class="header-banner"><h1>👥 الأصدقاء</h1></div>', unsafe_allow_html=True)
    with st.form("add_friend"):
        fu = st.text_input("اسم المستخدم")
        if st.form_submit_button("إرسال طلب"):
            if fu and fu != st.session_state.username:
                if add_friend(st.session_state.username, fu): st.success("تم")
                else: st.error("موجود مسبقاً")
            st.rerun()
    friends = get_friends(st.session_state.username)
    if not friends: st.info("لا أصدقاء")
    for f in friends:
        st.markdown(f"**{f['friend_username']}** — {f['status']}")
        if st.button("إزالة", key=f"rm_{f['id']}"):
            remove_friend(st.session_state.username, f["friend_username"]); st.rerun()
    footer()

# ============================================================
# LEADERBOARD
# ============================================================

def render_leaderboard():
    st.markdown('<div class="header-banner"><h1>🏆 المتصدرون</h1></div>', unsafe_allow_html=True)
    period = st.radio("الفترة", ["all", "week", "month"], horizontal=True,
                      format_func=lambda x: {"all": "الكل", "week": "الأسبوع", "month": "الشهر"}[x])
    board = get_leaderboard(period)
    if not board: st.info("لا بيانات")
    for i, row in enumerate(board):
        medal = ["🥇", "🥈", "🥉"][i] if i < 3 else f"#{i+1}"
        st.markdown(f"{medal} **{row['full_name'] or row['username']}** — {row['pts']} نقطة")
    footer()

# ============================================================
# WEEKLY
# ============================================================

def render_progress_chart(u):
    history = get_quiz_history(u, 30)
    if not history: st.info("لا سجل"); return
    data = [{"date": h["created_at"][:10], "percent": h["percent"]} for h in reversed(list(history))]
    try:
        import pandas as pd
        df = pd.DataFrame(data).groupby("date").mean().reset_index()
        st.line_chart(df.set_index("date")["percent"])
    except ImportError:
        for d in data[-10:]: st.write(f"{d['date']}: {d['percent']:.1f}%")

def render_weekly_report():
    st.markdown('<div class="header-banner"><h1>📊 التقرير الأسبوعي</h1></div>', unsafe_allow_html=True)
    report = get_weekly_report(st.session_state.username)
    if report:
        c1, c2, c3 = st.columns(3)
        with c1: st.metric("الاختبارات", report["cnt"])
        with c2: st.metric("النقاط", report["total_score"])
        with c3: st.metric("المعدل", f"{report['avg_pct']:.1f}%")
    st.markdown("### 📈 تطور الأداء")
    render_progress_chart(st.session_state.username)
    st.markdown("### 📊 إحصائيات المواد")
    for s in get_subject_stats(st.session_state.username):
        subj = SUBJECTS.get(s["subject"], {"name": s["subject"], "icon": "📖"})
        st.markdown(f"{subj['icon']} **{subj['name']}** — {s['cnt']} اختبار — {s['avg_pct']:.1f}%")
    st.markdown("### ⚠️ نقاط الضعف")
    weak = get_weaknesses(st.session_state.username)
    if weak:
        for w in weak:
            subj = SUBJECTS.get(w["subject"], {"name": w["subject"]})
            st.warning(f"{subj['name']} — {w['avg_pct']:.1f}%")
    else:
        st.success("لا نقاط ضعف")
    footer()

# ============================================================
# NOTIFICATIONS
# ============================================================

def render_notifications():
    st.markdown('<div class="header-banner"><h1>🔔 الإشعارات</h1></div>', unsafe_allow_html=True)
    notifs = get_notifications(st.session_state.username)
    if not notifs: st.info("لا إشعارات")
    for n in notifs:
        read = "" if n["is_read"] else "🟢 "
        st.markdown(f"{read}{n['icon']} **{n['title']}** — {n['message']} _({n['created_at'][:16]})_")
    if st.button("تعليم الكل"):
        mark_notifications_read(st.session_state.username); st.rerun()
    footer()

# ============================================================
# MY STATS
# ============================================================

def render_achievement_tracker():
    st.markdown("### 🎯 تتبع الإنجازات")
    stats = get_user_stats(st.session_state.username)
    if not stats: return
    prog = [
        ("أول اختبار", row_get(stats, "quizzes_taken"), 1),
        ("5 اختبارات", row_get(stats, "quizzes_taken"), 5),
        ("10 اختبارات", row_get(stats, "quizzes_taken"), 10),
        ("25 اختبار", row_get(stats, "quizzes_taken"), 25),
        ("50 اختبار", row_get(stats, "quizzes_taken"), 50),
        ("المستوى 5", row_get(stats, "level", 1), 5),
        ("المستوى 10", row_get(stats, "level", 1), 10),
        ("المستوى 20", row_get(stats, "level", 1), 20),
        ("7 مواد", row_get(stats, "unique_subjects"), 7),
        ("سلسلة 7 أيام", row_get(stats, "streak"), 7),
        ("10 تحميلات", row_get(stats, "files_downloaded"), 10),
        ("25 قراءة", row_get(stats, "files_read"), 25),
    ]
    for name, cur, tgt in prog:
        cur = cur or 0
        pct = min(cur / tgt, 1.0) if tgt else 0
        st.markdown(f"**{name}** — {min(cur, tgt)}/{tgt}")
        st.progress(pct)

def render_my_stats():
    st.markdown('<div class="header-banner"><h1>📈 إحصائياتي</h1></div>', unsafe_allow_html=True)
    stats = get_user_stats(st.session_state.username)
    if stats:
        c1, c2, c3, c4, c5 = st.columns(5)
        with c1: st.metric("النقاط", row_get(stats, "total_points"))
        with c2: st.metric("المستوى", row_get(stats, "level", 1))
        with c3: st.metric("الاختبارات", row_get(stats, "quizzes_taken"))
        with c4: st.metric("تحميلات", row_get(stats, "files_downloaded"))
        with c5: st.metric("قراءات", row_get(stats, "files_read"))
        st.markdown(f"**اللقب:** {get_rank(row_get(stats, 'level', 1))} — **السلسلة:** {row_get(stats, 'streak')} يوم")
    render_achievement_tracker()
    st.markdown("### 🏅 الشارات")
    earned = get_user_badges(st.session_state.username)
    cols = st.columns(4)
    for i, (key, name) in enumerate(BADGES.items()):
        with cols[i % 4]:
            if key in earned:
                st.markdown(f'<div class="badge badge-earned">{name}</div>', unsafe_allow_html=True)
            else:
                st.markdown(f'<div class="badge" style="opacity:0.4;">🔒 {name}</div>', unsafe_allow_html=True)
    st.markdown("### 📜 سجل الاختبارات")
    for h in get_quiz_history(st.session_state.username, 20):
        st.markdown(f"**{h['lesson_title']}** — {h['score']}/{h['total']} ({h['percent']:.1f}%) — {h['created_at'][:16]}")
    st.markdown("### 📈 تطور الأداء")
    render_progress_chart(st.session_state.username)
    footer()

# ============================================================
# FAVORITES
# ============================================================

def render_favorites():
    st.markdown('<div class="header-banner"><h1>❤️ المفضلة</h1></div>', unsafe_allow_html=True)
    favs = get_favorites(st.session_state.username)
    if not favs: st.info("لا يوجد")
    for l in favs:
        subj = SUBJECTS.get(l["subject"], {"name": l["subject"], "icon": "📖"})
        st.markdown(f"**{subj['icon']} {l['title']}**")
        if st.button(f"فتح", key=f"open_fav_{l['id']}"):
            st.session_state.view_lesson_id = l["id"]
            st.session_state.page = "lesson_view"; st.rerun()
    footer()

# ============================================================
# DEVELOPER
# ============================================================

def render_developer_panel():
    st.markdown('<div class="header-banner"><h1>🛠️ لوحة المطور</h1></div>', unsafe_allow_html=True)
    tabs = st.tabs(["📚 الدروس", "❓ الأسئلة", "📂 الملفات", "📦 الحزم", "👥 المستخدمون", "📊 إحصائيات"])
    with tabs[0]:
        with st.expander("➕ إضافة درس"):
            with st.form("add_lesson_form"):
                subject = st.selectbox("المادة", list(SUBJECTS.keys()),
                                       format_func=lambda x: f"{SUBJECTS[x]['icon']} {SUBJECTS[x]['name']}")
                level = st.selectbox("المستوى", list(LEVELS.keys()), format_func=lambda x: LEVELS[x])
                language = st.selectbox("اللغة", ["ar", "fr", "en"])
                title = st.text_input("العنوان *")
                content = st.text_area("المحتوى")
                image_url = st.text_input("رابط صورة")
                if st.form_submit_button("إضافة"):
                    if title:
                        add_lesson(subject, language, title, content, image_url, None,
                                   st.session_state.username, level)
                        st.success("تم"); st.rerun()
        lessons = load_lessons()
        st.markdown(f"**إجمالي الدروس:** {len(lessons)}")
        for l in lessons:
            subj = SUBJECTS.get(l["subject"], {"icon": "📖"})
            with st.expander(f"{subj['icon']} {l['title']}"):
                smart_text(l["content"])
                if st.button("🗑️ حذف", key=f"del_les_{l['id']}"):
                    delete_lesson(l["id"]); st.rerun()
    with tabs[1]:
        with st.expander("➕ إضافة سؤال"):
            lessons = load_lessons()
            if lessons:
                with st.form("add_question_form"):
                    opts = {l["id"]: f"{l['title']} ({l['subject']})" for l in lessons}
                    lid = st.selectbox("الدرس", list(opts.keys()), format_func=lambda x: opts[x])
                    q = st.text_input("السؤال")
                    a = st.text_input("أ"); b = st.text_input("ب"); c_opt = st.text_input("ج"); d = st.text_input("د")
                    correct = st.selectbox("الإجابة", ["a", "b", "c", "d"])
                    expl = st.text_area("الشرح")
                    if st.form_submit_button("إضافة"):
                        if q and a and b and c_opt and d:
                            add_question(lid, q, a, b, c_opt, d, correct, expl)
                            st.success("تم"); st.rerun()
        for l in load_lessons():
            qs = load_questions(l["id"])
            if qs:
                st.markdown(f"**{l['title']}** ({len(qs)})")
                for q in qs:
                    with st.expander(q["question"]):
                        st.write(f"أ) {q['option_a']} / ب) {q['option_b']} / ج) {q['option_c']} / د) {q['option_d']}")
                        st.success(f"✅ {q['correct_answer']}")
                        if st.button("🗑️", key=f"dq_{q['id']}"):
                            delete_question(q["id"]); st.rerun()
    with tabs[2]:
        st.markdown("### 📂 رفع ملف جديد")
        with st.form("dev_upload_file"):
            title = st.text_input("العنوان *")
            subject = st.selectbox("المادة", list(SUBJECTS.keys()),
                                   format_func=lambda x: f"{SUBJECTS[x]['icon']} {SUBJECTS[x]['name']}", key="df_subj")
            category = st.selectbox("النوع", ["files", "lessons", "exercises", "summaries", "books", "images", "models"],
                                    key="df_cat")
            level = st.selectbox("المستوى", list(LEVELS.keys()), format_func=lambda x: LEVELS[x], key="df_lvl")
            description = st.text_area("الوصف")
            tags = st.text_input("Tags")
            uploaded = st.file_uploader("اختر الملف *", key="df_file")
            if st.form_submit_button("⬆️ رفع"):
                if title and uploaded:
                    path = upload_file(uploaded, "files")
                    size = os.path.getsize(path) if path else 0
                    add_file_record(subject, category, title, description, path, uploaded.name,
                                    size, uploaded.type or "", st.session_state.username, level, tags)
                    st.success("تم"); st.rerun()
        st.markdown("### 📋 قائمة الملفات")
        all_files = get_files()
        st.markdown(f"إجمالي: **{len(all_files)}**")
        for f in all_files:
            subj = SUBJECTS.get(f["subject"], {"icon": "📄"})
            icon = get_file_icon(f["file_type"], f["file_name"])
            with st.expander(f"{icon} {f['title']} — {subj['name']}"):
                st.write(f"**النوع:** {f['category']} — **المستوى:** {f['level'] or 'intermediate'}")
                st.write(f"**الحجم:** {format_size(f['file_size'])} — **تحميلات:** {f['downloads'] or 0} — **قراءات:** {f['reads'] or 0}")
                st.markdown("**🔗 ربط بدرس:**")
                lessons = load_lessons()
                if lessons:
                    with st.form(f"link_to_lesson_{f['id']}"):
                        lopts = {l["id"]: l["title"] for l in lessons}
                        chosen = st.selectbox("الدرس", list(lopts.keys()),
                                              format_func=lambda x: lopts[x], key=f"ls_{f['id']}")
                        if st.form_submit_button("🔗 ربط"):
                            if link_file_to_lesson(chosen, f["id"], st.session_state.username):
                                st.success("تم الربط"); st.rerun()
                c1, c2, c3 = st.columns(3)
                with c1:
                    make_download_button(f["file_path"], f["file_name"], f"devdl_{f['id']}", "📥")
                with c2:
                    if st.button("📌", key=f"pin_{f['id']}"):
                        pin_file(f["id"]); st.rerun()
                with c3:
                    if st.button("🗑️ حذف", key=f"delf_{f['id']}"):
                        delete_file_record(f["id"]); st.rerun()
    with tabs[3]:
        st.markdown("### 📦 إنشاء حزمة")
        with st.form("dev_create_coll"):
            title = st.text_input("العنوان *")
            desc = st.text_area("الوصف")
            subject = st.selectbox("المادة", list(SUBJECTS.keys()),
                                   format_func=lambda x: SUBJECTS[x]["name"], key="dc_subj")
            icon = st.text_input("الأيقونة", "📦")
            if st.form_submit_button("إنشاء"):
                if title:
                    add_collection(title, desc, subject, icon, st.session_state.username)
                    st.success("تم"); st.rerun()
        for cl in get_collections():
            st.markdown(f"**{cl['icon']} {cl['title']}** — {len(get_collection_items(cl['id']))} عنصر")
            if st.button("🗑️", key=f"dcl_{cl['id']}"):
                delete_collection(cl["id"]); st.rerun()
    with tabs[4]:
        conn = get_db()
        c = conn.cursor()
        c.execute("SELECT * FROM users ORDER BY created_at DESC")
        users = c.fetchall()
        conn.close()
        st.markdown(f"**إجمالي:** {len(users)}")
        for u in users:
            st.markdown(f"**{u['username']}** — {u['full_name']} — {u['role']} — {u['created_at'][:10]}")
    with tabs[5]:
        conn = get_db()
        c = conn.cursor()
        c.execute("SELECT COUNT(*) as cnt FROM lessons"); lc = c.fetchone()["cnt"]
        c.execute("SELECT COUNT(*) as cnt FROM questions"); qc = c.fetchone()["cnt"]
        c.execute("SELECT COUNT(*) as cnt FROM files"); fc = c.fetchone()["cnt"]
        c.execute("SELECT COUNT(*) as cnt FROM users"); uc = c.fetchone()["cnt"]
        c.execute("SELECT COUNT(*) as cnt FROM collections"); cc = c.fetchone()["cnt"]
        c.execute("SELECT COUNT(*) as cnt FROM download_log"); dc = c.fetchone()["cnt"]
        c.execute("SELECT category, COUNT(*) as cnt FROM files GROUP BY category")
        cats = c.fetchall()
        conn.close()
        c1, c2, c3, c4, c5, c6 = st.columns(6)
        with c1: st.metric("دروس", lc)
        with c2: st.metric("أسئلة", qc)
        with c3: st.metric("ملفات", fc)
        with c4: st.metric("مستخدمون", uc)
        with c5: st.metric("حزم", cc)
        with c6: st.metric("تحميلات", dc)
        st.markdown("### 📊 حسب النوع")
        for cat in cats:
            st.markdown(f"- **{cat['category']}**: {cat['cnt']}")
        st.markdown("### 🔥 الأكثر تحميلاً")
        for f in get_files(sort="downloads")[:5]:
            st.markdown(f"- {f['title']} — {f['downloads'] or 0} تحميل")
    footer()

# ============================================================
# SIDEBAR
# ============================================================

def render_sidebar():
    with st.sidebar:
        st.markdown(f"### 👤 {st.session_state.full_name or st.session_state.username}")
        stats = get_user_stats(st.session_state.username)
        if stats:
            lvl = row_get(stats, "level", 1)
            pts = row_get(stats, "total_points", 0)
            st.markdown(f"**{get_rank(lvl)}** — L{lvl}")
            st.progress((pts % 100) / 100)
        
        with st.expander("🎨 الثيم والإعدادات", expanded=False):
            theme_keys = list(THEMES.keys())
            theme_names = [THEMES[k]["name"] for k in theme_keys]
            cur = st.session_state.get("theme", "fcb")
            idx = theme_keys.index(cur) if cur in theme_keys else 0
            sel = st.selectbox("الثيم", theme_names, index=idx, key="theme_select")
            st.session_state.theme = theme_keys[theme_names.index(sel)]
        
        st.divider()
        
        # Group 1: Learning content
        with st.expander("📖 المحتوى التعليمي", expanded=True):
            for key, icon, label in [
                ("dashboard", "🏠", "الرئيسية"),
                ("lessons", "📖", "الدروس"),
                ("files", "📂", "الملفات"),
                ("collections", "📦", "الحزم"),
            ]:
                if st.button(f"{icon} {label}", key=f"nav_{key}", use_container_width=True):
                    st.session_state.page = key; st.rerun()
        
        # Group 2: Learning
        with st.expander("🎓 التعلّم والمراجعة", expanded=False):
            for key, icon, label in [
                ("daily_challenge", "🎯", "التحدي اليومي"),
                ("quick_review", "⚡", "مراجعة سريعة"),
                ("pomodoro", "⏱️", "مؤقت المراجعة"),
                ("flashcards", "🃏", "بطاقات"),
            ]:
                if st.button(f"{icon} {label}", key=f"nav_{key}", use_container_width=True):
                    st.session_state.page = key; st.rerun()
        
        # Group 3: Tracking
        with st.expander("📊 المتابعة", expanded=False):
            for key, icon, label in [
                ("study_plan", "📅", "خطة الدراسة"),
                ("leaderboard", "🏆", "المتصدرون"),
                ("weekly_report", "📊", "التقرير الأسبوعي"),
                ("my_stats", "📈", "إحصائياتي"),
            ]:
                if st.button(f"{icon} {label}", key=f"nav_{key}", use_container_width=True):
                    st.session_state.page = key; st.rerun()
        
        # Group 4: Social
        with st.expander("👤 الاجتماعي", expanded=False):
            for key, icon, label in [
                ("friends", "👥", "الأصدقاء"),
                ("notifications", "🔔", "الإشعارات"),
                ("favorites", "❤️", "المفضلة"),
            ]:
                if st.button(f"{icon} {label}", key=f"nav_{key}", use_container_width=True):
                    st.session_state.page = key; st.rerun()
        
        # Group 5: Dev
        if st.session_state.role == "developer":
            with st.expander("🛠️ الإدارة", expanded=False):
                if st.button("🛠️ لوحة المطور", key="nav_developer_panel", use_container_width=True):
                    st.session_state.page = "developer_panel"; st.rerun()
        
        st.divider()
        unread = get_notifications(st.session_state.username, unread=True)
        if unread:
            st.info(f"🔔 {len(unread)} جديد")
        if st.button("🚪 تسجيل الخروج", use_container_width=True):
            for k in list(st.session_state.keys()): del st.session_state[k]
            st.rerun()

# ============================================================
# MAIN
# ============================================================

init_db()

defaults = {"theme": "fcb", "authenticated": False, "page": "dashboard"}
for k, v in defaults.items():
    if k not in st.session_state:
        st.session_state[k] = v

st.set_page_config(page_title="3AC RevisioMaroc", page_icon="📚", layout="wide")
apply_theme()

if not st.session_state.authenticated:
    render_auth_page()
    st.stop()

render_sidebar()

page = st.session_state.get("page", "dashboard")
routes = {
    "dashboard": render_dashboard,
    "lessons": render_lessons,
    "lesson_view": render_lesson_view,
    "files": render_files,
    "file_view": render_file_view,
    "collections": render_collections,
    "collection_view": render_collection_view,
    "search_results": render_search_results,
    "quiz": render_quiz,
    "daily_challenge": render_daily_challenge,
    "pomodoro": render_pomodoro_page,
    "quick_review": render_quick_review,
    "flashcards": render_flashcards,
    "study_plan": render_study_plan,
    "friends": render_friends,
    "leaderboard": render_leaderboard,
    "weekly_report": render_weekly_report,
    "notifications": render_notifications,
    "my_stats": render_my_stats,
    "favorites": render_favorites,
}
if page == "developer_panel":
    if st.session_state.role == "developer":
        render_developer_panel()
    else:
        st.error("غير مصرح")
else:
    routes.get(page, render_dashboard)()
