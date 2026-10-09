# -*- coding: utf-8 -*-
"""
3AC RevisioMaroc — تطبيق Streamlit للمراجعة (الجذع المشترك)
تشغيل:  streamlit run app.py
"""
import streamlit as st
import hashlib
import sqlite3
import os
import base64
import random
import time
import json
from datetime import datetime, timedelta, date
from pathlib import Path

# ════════════════════════════════════════════════════════════
#  إعداد الصفحة
# ════════════════════════════════════════════════════════════
st.set_page_config(
    page_title="3AC RevisioMaroc",
    page_icon="📚",
    layout="wide",
    initial_sidebar_state="expanded",
)

DB_PATH = "revisiomaroc.db"
UPLOAD_DIR = Path("uploads")
QUIZ_DURATION = 600  # 10 دقائق
FOOTER_TEXT = "© 2026 Soufiane Ouhazza — 3AC RevisioMaroc"

# ════════════════════════════════════════════════════════════
#  الثوابت
# ════════════════════════════════════════════════════════════
SUBJECTS = {
    "maths":   {"name": "الرياضيات",            "icon": "📐", "color": "#4A90E2"},
    "french":  {"name": "اللغة الفرنسية",       "icon": "🇫🇷", "color": "#E74C3C"},
    "english": {"name": "اللغة الإنجليزية",     "icon": "🇬🇧", "color": "#3498DB"},
    "history": {"name": "الاجتماعيات",          "icon": "🌍", "color": "#F39C12"},
    "islamic": {"name": "التربية الإسلامية",    "icon": "🕌", "color": "#27AE60"},
    "pc":      {"name": "الفيزياء والكيمياء",   "icon": "⚗️", "color": "#9B59B6"},
    "svt":     {"name": "علوم الحياة والأرض",   "icon": "🧬", "color": "#16A085"},
}

LANGS = {"ar": "🇲🇦 العربية", "fr": "🇫🇷 Français", "en": "🇬🇧 English"}
LESSON_LANGS = {"ar": "العربية", "fr": "Français", "en": "English"}

THEMES = {
    "⚽ FC Barcelona": {"bg": "#0A1E3F", "card": "#1A2F5C", "text": "#F0F8FF", "accent": "#A50044", "secondary": "#0F2A52", "border": "#004D98", "highlight": "#00D26A"},
    "👑 Real Madrid": {"bg": "#0F1B2D", "card": "#1E2E4A", "text": "#FFFFFF", "accent": "#FEBE10", "secondary": "#0A1421", "border": "#00529F", "highlight": "#FEBE10"},
    "🦅 الأهلي": {"bg": "#1A0A0A", "card": "#2D1515", "text": "#FFF5F5", "accent": "#E30613", "secondary": "#120505", "border": "#8B0000", "highlight": "#FFD700"},
    "🌙 Moonlight": {"bg": "#0A0E1A", "card": "#1A1F35", "text": "#E8ECFF", "accent": "#7B9FFF", "secondary": "#050810", "border": "#3D4A7A", "highlight": "#FFE57F"},
    "🌙 Midnight Purple": {"bg": "#0D0B1F", "card": "#1A1735", "text": "#EDE9FE", "accent": "#A78BFA", "secondary": "#221D4A", "border": "#3D3475", "highlight": "#4ADE80"},
    "🌊 Ocean Deep": {"bg": "#0A1929", "card": "#132F4C", "text": "#E3F2FD", "accent": "#00B8D4", "secondary": "#0F2537", "border": "#1E4976", "highlight": "#4ADE80"},
    "📚 Study Mode": {"bg": "#1A1410", "card": "#2D2418", "text": "#FFF8E7", "accent": "#D4A574", "secondary": "#0F0B07", "border": "#5C4A2E", "highlight": "#FFD700"},
    "🌅 Golden Sunset": {"bg": "#1F1410", "card": "#331F17", "text": "#FFF3E0", "accent": "#FFB74D", "secondary": "#2A1A12", "border": "#5D3A24", "highlight": "#4ADE80"},
    "🌿 Forest Emerald": {"bg": "#0B1F14", "card": "#143728", "text": "#E8F5E9", "accent": "#4ADE80", "secondary": "#0F2A1D", "border": "#1E5C3D", "highlight": "#00D26A"},
    "☀️ Light Mode": {"bg": "#F5F7FA", "card": "#FFFFFF", "text": "#1A202C", "accent": "#4A90E2", "secondary": "#E2E8F0", "border": "#CBD5E0", "highlight": "#38A169"},
    "🌌 Galaxy": {"bg": "#0D0221", "card": "#1A0533", "text": "#E8D5FF", "accent": "#C77DFF", "secondary": "#050011", "border": "#7209B7", "highlight": "#4CC9F0"},
}

BADGES = {
    "first_quiz": "🎯 أول اختبار",
    "perfect": "💯 العلامة الكاملة",
    "5_quizzes": "🔥 مجتهد",
    "10_quizzes": "💪 مثابر",
    "25_quizzes": "🏃 عدّاء",
    "50_quizzes": "🚀 صاروخ",
    "100_quizzes": "🌟 أسطورة",
    "level_5": "⭐ نجم",
    "level_10": "🌟 نجم لامع",
    "level_20": "👑 ملك",
    "level_50": "🏆 أسطورة حية",
    "all_subjects": "🎓 الموسوعي",
    "streak_7": "🔥 أسبوع كامل",
    "streak_30": "🌋 شهر كامل",
}

RANKS = {
    1: "🌱 مبتدئ",
    3: "📖 متعلّم",
    5: "🎯 مجتهد",
    8: "⭐ متميز",
    12: "🏅 متفوق",
    20: "👑 خبير",
    35: "🏆 أسطورة",
    50: "🌟 أسطورة حية",
}

PRIORITIES = {"high": "🔴 عالية", "medium": "🟡 متوسطة", "low": "🟢 منخفضة"}

PAGES = [
    "dashboard", "lessons", "quiz", "quick_review", "flashcards", "study_plan",
    "friends", "leaderboard", "weekly_report", "notifications", "my_stats", "favorites",
]
PAGE_ICONS = {
    "dashboard": "🏠", "lessons": "📚", "quiz": "📝", "quick_review": "⚡",
    "flashcards": "🃏", "study_plan": "🗓️", "friends": "👥", "leaderboard": "🏆",
    "weekly_report": "📈", "notifications": "🔔", "my_stats": "📊", "favorites": "⭐",
    "dev_panel": "🛠️",
}

# ════════════════════════════════════════════════════════════
#  الترجمة   (ar, fr, en)
# ════════════════════════════════════════════════════════════
TR = {
    "app_name": ("3AC RevisioMaroc", "3AC RevisioMaroc", "3AC RevisioMaroc"),
    "dashboard": ("الرئيسية", "Accueil", "Home"),
    "lessons": ("الدروس", "Cours", "Lessons"),
    "quiz": ("الاختبار", "Quiz", "Quiz"),
    "quick_review": ("مراجعة سريعة", "Révision rapide", "Quick Review"),
    "flashcards": ("البطاقات", "Flashcards", "Flashcards"),
    "study_plan": ("خطة المراجعة", "Plan d'étude", "Study Plan"),
    "friends": ("الأصدقاء", "Amis", "Friends"),
    "leaderboard": ("الترتيب", "Classement", "Leaderboard"),
    "weekly_report": ("التقرير الأسبوعي", "Rapport hebdo", "Weekly Report"),
    "notifications": ("الإشعارات", "Notifications", "Notifications"),
    "my_stats": ("إحصائياتي", "Mes stats", "My Stats"),
    "favorites": ("المفضلة", "Favoris", "Favorites"),
    "dev_panel": ("لوحة المطور", "Panneau dév.", "Developer Panel"),
    "theme": ("🎨 الثيم", "🎨 Thème", "🎨 Theme"),
    "language": ("🌐 اللغة", "🌐 Langue", "🌐 Language"),
    "menu": ("📋 القائمة", "📋 Menu", "📋 Menu"),
    "logout": ("🚪 تسجيل الخروج", "🚪 Déconnexion", "🚪 Logout"),
    "login": ("تسجيل الدخول", "Connexion", "Login"),
    "register": ("إنشاء حساب", "Créer un compte", "Register"),
    "username": ("اسم المستخدم", "Nom d'utilisateur", "Username"),
    "password": ("كلمة المرور", "Mot de passe", "Password"),
    "full_name": ("الاسم الكامل", "Nom complet", "Full name"),
    "student": ("تلميذ", "Élève", "Student"),
    "developer": ("مطور", "Développeur", "Developer"),
    "back": ("⬅️ رجوع", "⬅️ Retour", "⬅️ Back"),
    "points": ("النقاط", "Points", "Points"),
    "level": ("المستوى", "Niveau", "Level"),
    "rank": ("اللقب", "Titre", "Rank"),
    "streak": ("التتابع", "Série", "Streak"),
    "quizzes": ("الاختبارات", "Quiz passés", "Quizzes"),
    "search": ("🔍 بحث", "🔍 Recherche", "🔍 Search"),
    "all": ("الكل", "Tous", "All"),
    "subject": ("المادة", "Matière", "Subject"),
    "start_quiz": ("📝 ابدأ الاختبار", "📝 Commencer le quiz", "📝 Start quiz"),
    "submit": ("✅ تسليم", "✅ Envoyer", "✅ Submit"),
    "welcome": ("مرحباً", "Bienvenue", "Welcome"),
}


def T(key):
    lang = st.session_state.get("lang", "ar")
    idx = {"ar": 0, "fr": 1, "en": 2}.get(lang, 0)
    val = TR.get(key)
    if not val:
        return key
    return val[idx] or val[0]


# ════════════════════════════════════════════════════════════
#  قاعدة البيانات
# ════════════════════════════════════════════════════════════
def get_db():
    conn = sqlite3.connect(DB_PATH, check_same_thread=False)
    conn.row_factory = sqlite3.Row
    return conn


def db_exec(sql, params=(), fetch=None, commit=False):
    conn = get_db()
    try:
        cur = conn.execute(sql, params)
        if commit:
            conn.commit()
        if fetch == "one":
            r = cur.fetchone()
            return dict(r) if r else None
        if fetch == "all":
            return [dict(r) for r in cur.fetchall()]
        return cur.lastrowid
    finally:
        conn.close()


def hash_password(p):
    return hashlib.sha256(p.encode("utf-8")).hexdigest()


def init_db():
    conn = get_db()
    try:
        conn.executescript("""
        CREATE TABLE IF NOT EXISTS users (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            username TEXT UNIQUE NOT NULL,
            password_hash TEXT NOT NULL,
            role TEXT NOT NULL DEFAULT 'student',
            full_name TEXT,
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
        );
        CREATE TABLE IF NOT EXISTS lessons (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            subject TEXT NOT NULL,
            language TEXT NOT NULL DEFAULT 'ar',
            title TEXT NOT NULL,
            content TEXT,
            image_url TEXT,
            pdf_url TEXT,
            owner TEXT,
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
        );
        CREATE TABLE IF NOT EXISTS questions (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            lesson_id INTEGER NOT NULL,
            question TEXT NOT NULL,
            option_a TEXT, option_b TEXT, option_c TEXT, option_d TEXT,
            correct_answer TEXT NOT NULL,
            explanation TEXT
        );
        CREATE TABLE IF NOT EXISTS quiz_history (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            username TEXT NOT NULL,
            lesson_id INTEGER,
            lesson_title TEXT,
            subject TEXT,
            score INTEGER,
            total INTEGER,
            percent REAL,
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
        );
        CREATE TABLE IF NOT EXISTS favorites (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            username TEXT NOT NULL,
            lesson_id INTEGER NOT NULL,
            UNIQUE(username, lesson_id)
        );
        CREATE TABLE IF NOT EXISTS user_stats (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            username TEXT UNIQUE NOT NULL,
            total_points INTEGER DEFAULT 0,
            level INTEGER DEFAULT 1,
            quizzes_taken INTEGER DEFAULT 0,
            perfect_scores INTEGER DEFAULT 0,
            unique_subjects TEXT DEFAULT '',
            badges TEXT DEFAULT '[]',
            last_daily TEXT DEFAULT '',
            streak INTEGER DEFAULT 0
        );
        CREATE TABLE IF NOT EXISTS reviews (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            lesson_id INTEGER NOT NULL,
            username TEXT NOT NULL,
            rating INTEGER NOT NULL,
            comment TEXT,
            UNIQUE(lesson_id, username)
        );
        CREATE TABLE IF NOT EXISTS messages (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            lesson_id INTEGER NOT NULL,
            username TEXT NOT NULL,
            message TEXT NOT NULL
        );
        CREATE TABLE IF NOT EXISTS notifications (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            username TEXT NOT NULL,
            title TEXT,
            message TEXT,
            icon TEXT DEFAULT '🔔',
            is_read INTEGER DEFAULT 0
        );
        CREATE TABLE IF NOT EXISTS flashcards (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            username TEXT NOT NULL,
            subject TEXT,
            front TEXT NOT NULL,
            back TEXT NOT NULL,
            known INTEGER DEFAULT 0
        );
        CREATE TABLE IF NOT EXISTS notes (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            username TEXT NOT NULL,
            lesson_id INTEGER NOT NULL,
            note TEXT NOT NULL
        );
        CREATE TABLE IF NOT EXISTS friends (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            username TEXT NOT NULL,
            friend_username TEXT NOT NULL,
            status TEXT DEFAULT 'accepted',
            UNIQUE(username, friend_username)
        );
        CREATE TABLE IF NOT EXISTS study_plan (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            username TEXT NOT NULL,
            subject TEXT,
            priority TEXT DEFAULT 'medium',
            target_date TEXT,
            completed INTEGER DEFAULT 0
        );
        """)
        conn.commit()
        row = conn.execute("SELECT id FROM users WHERE username=?", ("soufianeDEV",)).fetchone()
        if not row:
            conn.execute(
                "INSERT INTO users (username, password_hash, role, full_name) VALUES (?,?,?,?)",
                ("soufianeDEV", hash_password("soufiane2030"), "developer", "Soufiane Ouhazza"),
            )
            conn.commit()
    finally:
        conn.close()
    UPLOAD_DIR.mkdir(exist_ok=True)


# ════════════════════════════════════════════════════════════
#  المستخدمون
# ════════════════════════════════════════════════════════════
def register_user(u, p, n):
    u = (u or "").strip()
    n = (n or "").strip()
    if len(u) < 3:
        return False, "اسم المستخدم لازم يكون 3 حروف على الأقل"
    if len(p or "") < 6:
        return False, "كلمة المرور لازم تكون 6 حروف على الأقل"
    if not n:
        return False, "المرجو إدخال الاسم الكامل"
    if db_exec("SELECT id FROM users WHERE username=?", (u,), "one"):
        return False, "اسم المستخدم مستعمل من قبل"
    db_exec(
        "INSERT INTO users (username, password_hash, role, full_name) VALUES (?,?,?,?)",
        (u, hash_password(p), "student", n), commit=True,
    )
    db_exec("INSERT OR IGNORE INTO user_stats (username) VALUES (?)", (u,), commit=True)
    add_notification(u, "مرحباً بك 🎉", "تم إنشاء حسابك بنجاح. بالتوفيق في المراجعة!", "🎉")
    return True, "تم إنشاء الحساب بنجاح"


def authenticate(u, p):
    r = db_exec(
        "SELECT * FROM users WHERE username=? AND password_hash=?",
        ((u or "").strip(), hash_password(p or "")), "one",
    )
    return r


def get_user_stats(u):
    r = db_exec("SELECT * FROM user_stats WHERE username=?", (u,), "one")
    if not r:
        db_exec("INSERT OR IGNORE INTO user_stats (username) VALUES (?)", (u,), commit=True)
        r = db_exec("SELECT * FROM user_stats WHERE username=?", (u,), "one")
    r["level"] = (r["total_points"] or 0) // 100 + 1
    try:
        r["badges_list"] = json.loads(r["badges"] or "[]")
    except Exception:
        r["badges_list"] = []
    r["subjects_list"] = [s for s in (r["unique_subjects"] or "").split(",") if s]
    return r


def update_user_stats(u, points=0, quiz=0, perfect=0, subject=None):
    s = get_user_stats(u)
    old_level = s["level"]
    total = (s["total_points"] or 0) + points
    subs = s["subjects_list"]
    if subject and subject not in subs:
        subs.append(subject)
    level = total // 100 + 1
    db_exec(
        "UPDATE user_stats SET total_points=?, level=?, quizzes_taken=quizzes_taken+?, "
        "perfect_scores=perfect_scores+?, unique_subjects=? WHERE username=?",
        (total, level, int(quiz), int(perfect), ",".join(subs), u), commit=True,
    )
    if level > old_level:
        add_notification(u, "ترقية في المستوى!", f"وصلتي للمستوى {level} — {get_rank(level)}", "🆙")
    check_badges(u)


# ════════════════════════════════════════════════════════════
#  الاختبارات والإحصائيات
# ════════════════════════════════════════════════════════════
def save_quiz_result(username, lesson_id, lesson_title, subject, score, total):
    percent = round((score / total) * 100, 1) if total else 0
    db_exec(
        "INSERT INTO quiz_history (username, lesson_id, lesson_title, subject, score, total, percent) "
        "VALUES (?,?,?,?,?,?,?)",
        (username, lesson_id, lesson_title, subject, score, total, percent), commit=True,
    )
    return percent


def get_quiz_history(u, limit=20):
    return db_exec(
        "SELECT * FROM quiz_history WHERE username=? ORDER BY id DESC LIMIT ?",
        (u, limit), "all",
    )


def get_subject_stats(u):
    rows = db_exec(
        "SELECT subject, COUNT(*) AS cnt, AVG(percent) AS avg_percent, MAX(percent) AS best "
        "FROM quiz_history WHERE username=? GROUP BY subject", (u,), "all",
    )
    return {r["subject"]: r for r in rows}


def get_weaknesses(u):
    stats = get_subject_stats(u)
    weak = [(s, d["avg_percent"]) for s, d in stats.items() if d["avg_percent"] is not None and d["avg_percent"] < 60]
    weak.sort(key=lambda x: x[1])
    return weak


def get_leaderboard(period="all"):
    if period == "week":
        rows = db_exec(
            "SELECT h.username, SUM(h.score)*10 AS points, COUNT(*) AS quizzes FROM quiz_history h "
            "JOIN users u ON u.username=h.username WHERE u.role='student' "
            "AND h.created_at >= datetime('now','-7 days') GROUP BY h.username "
            "ORDER BY points DESC LIMIT 20", (), "all")
    elif period == "month":
        rows = db_exec(
            "SELECT h.username, SUM(h.score)*10 AS points, COUNT(*) AS quizzes FROM quiz_history h "
            "JOIN users u ON u.username=h.username WHERE u.role='student' "
            "AND h.created_at >= datetime('now','-30 days') GROUP BY h.username "
            "ORDER BY points DESC LIMIT 20", (), "all")
    else:
        rows = db_exec(
            "SELECT s.username, s.total_points AS points, s.quizzes_taken AS quizzes FROM user_stats s "
            "JOIN users u ON u.username=s.username WHERE u.role='student' "
            "ORDER BY s.total_points DESC LIMIT 20", (), "all")
    for r in rows:
        usr = db_exec("SELECT full_name FROM users WHERE username=?", (r["username"],), "one")
        r["full_name"] = (usr or {}).get("full_name") or r["username"]
        r["points"] = r["points"] or 0
        r["level"] = r["points"] // 100 + 1 if period == "all" else None
    return rows


def get_weekly_report(u):
    agg = db_exec(
        "SELECT COUNT(*) AS cnt, AVG(percent) AS avg_percent, SUM(score) AS total_score, "
        "SUM(total) AS total_q FROM quiz_history WHERE username=? "
        "AND created_at >= datetime('now','-7 days')", (u,), "one",
    )
    by_subject = db_exec(
        "SELECT subject, COUNT(*) AS cnt, AVG(percent) AS avg_percent FROM quiz_history "
        "WHERE username=? AND created_at >= datetime('now','-7 days') GROUP BY subject "
        "ORDER BY avg_percent DESC", (u,), "all",
    )
    history = db_exec(
        "SELECT * FROM quiz_history WHERE username=? AND created_at >= datetime('now','-7 days') "
        "ORDER BY id DESC", (u,), "all",
    )
    return {
        "count": agg["cnt"] or 0,
        "avg": round(agg["avg_percent"] or 0, 1),
        "points": (agg["total_score"] or 0) * 10,
        "correct": agg["total_score"] or 0,
        "questions": agg["total_q"] or 0,
        "by_subject": by_subject,
        "history": history,
    }


def check_badges(u):
    s = get_user_stats(u)
    have = set(s["badges_list"])
    q = s["quizzes_taken"] or 0
    lvl = s["level"]
    cond = {
        "first_quiz": q >= 1,
        "perfect": (s["perfect_scores"] or 0) >= 1,
        "5_quizzes": q >= 5,
        "10_quizzes": q >= 10,
        "25_quizzes": q >= 25,
        "50_quizzes": q >= 50,
        "100_quizzes": q >= 100,
        "level_5": lvl >= 5,
        "level_10": lvl >= 10,
        "level_20": lvl >= 20,
        "level_50": lvl >= 50,
        "all_subjects": len(s["subjects_list"]) >= len(SUBJECTS),
        "streak_7": (s["streak"] or 0) >= 7,
        "streak_30": (s["streak"] or 0) >= 30,
    }
    new = [k for k, ok in cond.items() if ok and k not in have]
    if new:
        allb = list(have) + new
        db_exec("UPDATE user_stats SET badges=? WHERE username=?", (json.dumps(allb), u), commit=True)
        for k in new:
            add_notification(u, "شارة جديدة!", f"ربحتي شارة: {BADGES[k]}", "🏅")
    return new


def get_user_badges(u):
    return get_user_stats(u)["badges_list"]


def get_rank(lvl):
    title = RANKS[1]
    for th in sorted(RANKS):
        if lvl >= th:
            title = RANKS[th]
    return title


def can_claim_daily(u):
    s = get_user_stats(u)
    return (s["last_daily"] or "") != date.today().isoformat()


def check_daily_bonus(u):
    """يرجع (تم_الاستلام, النقاط, التتابع)"""
    s = get_user_stats(u)
    today = date.today()
    last = s["last_daily"] or ""
    if last == today.isoformat():
        return False, 0, s["streak"] or 0
    yesterday = (today - timedelta(days=1)).isoformat()
    streak = (s["streak"] or 0) + 1 if last == yesterday else 1
    bonus = min(50, 10 + (streak - 1) * 5)
    total = (s["total_points"] or 0) + bonus
    db_exec(
        "UPDATE user_stats SET total_points=?, level=?, last_daily=?, streak=? WHERE username=?",
        (total, total // 100 + 1, today.isoformat(), streak, u), commit=True,
    )
    add_notification(u, "مكافأة يومية 🎁", f"ربحتي {bonus} نقطة — التتابع: {streak} يوم", "🎁")
    if total // 100 + 1 > s["level"]:
        add_notification(u, "ترقية في المستوى!", f"وصلتي للمستوى {total // 100 + 1}", "🆙")
    check_badges(u)
    return True, bonus, streak


# ════════════════════════════════════════════════════════════
#  الإشعارات
# ════════════════════════════════════════════════════════════
def add_notification(u, title, msg, icon="🔔"):
    db_exec(
        "INSERT INTO notifications (username, title, message, icon) VALUES (?,?,?,?)",
        (u, title, msg, icon), commit=True,
    )


def get_notifications(u, unread=False):
    if unread:
        return db_exec(
            "SELECT * FROM notifications WHERE username=? AND is_read=0 ORDER BY id DESC", (u,), "all")
    return db_exec("SELECT * FROM notifications WHERE username=? ORDER BY id DESC LIMIT 100", (u,), "all")


def mark_notifications_read(u):
    db_exec("UPDATE notifications SET is_read=1 WHERE username=?", (u,), commit=True)


# ════════════════════════════════════════════════════════════
#  المفضلة
# ════════════════════════════════════════════════════════════
def toggle_favorite(u, lid):
    if is_favorite(u, lid):
        db_exec("DELETE FROM favorites WHERE username=? AND lesson_id=?", (u, lid), commit=True)
        return False
    db_exec("INSERT OR IGNORE INTO favorites (username, lesson_id) VALUES (?,?)", (u, lid), commit=True)
    return True


def is_favorite(u, lid):
    return db_exec(
        "SELECT id FROM favorites WHERE username=? AND lesson_id=?", (u, lid), "one") is not None


def get_favorites(u):
    return db_exec(
        "SELECT l.* FROM lessons l JOIN favorites f ON f.lesson_id=l.id "
        "WHERE f.username=? ORDER BY f.id DESC", (u,), "all")


# ════════════════════════════════════════════════════════════
#  الدروس والأسئلة
# ════════════════════════════════════════════════════════════
def load_lessons(subject=None, language=None, owner=None, search=None):
    sql = "SELECT * FROM lessons WHERE 1=1"
    params = []
    if subject and subject != "all":
        sql += " AND subject=?"
        params.append(subject)
    if language and language != "all":
        sql += " AND language=?"
        params.append(language)
    if owner:
        sql += " AND owner=?"
        params.append(owner)
    if search:
        sql += " AND (title LIKE ? OR content LIKE ?)"
        params += [f"%{search}%", f"%{search}%"]
    sql += " ORDER BY id DESC"
    return db_exec(sql, tuple(params), "all")


def get_lesson(lid):
    return db_exec("SELECT * FROM lessons WHERE id=?", (lid,), "one")


def add_lesson(subject, language, title, content, image_url, pdf_url, owner):
    return db_exec(
        "INSERT INTO lessons (subject, language, title, content, image_url, pdf_url, owner) "
        "VALUES (?,?,?,?,?,?,?)",
        (subject, language, title, content, image_url or "", pdf_url or "", owner), commit=True,
    )


def delete_lesson(lid, owner=None):
    l = get_lesson(lid)
    if not l:
        return False
    if owner and l["owner"] != owner:
        return False
    for tbl in ("questions", "favorites", "reviews", "messages", "notes"):
        db_exec(f"DELETE FROM {tbl} WHERE lesson_id=?", (lid,), commit=True)
    db_exec("DELETE FROM lessons WHERE id=?", (lid,), commit=True)
    return True


def load_questions(lid):
    return db_exec("SELECT * FROM questions WHERE lesson_id=? ORDER BY id", (lid,), "all")


def add_question(lesson_id, question, a, b, c, d, correct, explanation=""):
    return db_exec(
        "INSERT INTO questions (lesson_id, question, option_a, option_b, option_c, option_d, "
        "correct_answer, explanation) VALUES (?,?,?,?,?,?,?,?)",
        (lesson_id, question, a, b, c, d, correct.upper(), explanation), commit=True,
    )


def delete_question(qid):
    db_exec("DELETE FROM questions WHERE id=?", (qid,), commit=True)


def upload_file(f, folder):
    if f is None:
        return ""
    target = UPLOAD_DIR / folder
    target.mkdir(parents=True, exist_ok=True)
    safe = "".join(ch if ch.isalnum() or ch in "._-" else "_" for ch in f.name)
    path = target / f"{int(time.time())}_{safe}"
    with open(path, "wb") as out:
        out.write(f.getbuffer())
    return str(path)


def render_pdf(path, key="pdf"):
    if not path:
        return
    try:
        if os.path.exists(path):
            with open(path, "rb") as fh:
                data = fh.read()
            b64 = base64.b64encode(data).decode()
            st.markdown(
                f'<iframe src="data:application/pdf;base64,{b64}" width="100%" height="600" '
                f'style="border:1px solid var(--border);border-radius:10px;"></iframe>',
                unsafe_allow_html=True,
            )
            st.download_button("⬇️ تحميل PDF", data, file_name=os.path.basename(path),
                               mime="application/pdf", key=f"dl_{key}")
        elif path.startswith("http"):
            st.markdown(
                f'<iframe src="{path}" width="100%" height="600" '
                f'style="border:1px solid var(--border);border-radius:10px;"></iframe>',
                unsafe_allow_html=True,
            )
            st.link_button("🔗 فتح الملف", path)
        else:
            st.warning("ملف PDF غير موجود")
    except Exception as e:
        st.warning(f"تعذر عرض الملف: {e}")


# ════════════════════════════════════════════════════════════
#  التقييمات والنقاش
# ════════════════════════════════════════════════════════════
def add_review(lid, username, rating, comment):
    db_exec(
        "INSERT INTO reviews (lesson_id, username, rating, comment) VALUES (?,?,?,?) "
        "ON CONFLICT(lesson_id, username) DO UPDATE SET rating=excluded.rating, comment=excluded.comment",
        (lid, username, int(rating), comment), commit=True,
    )


def get_reviews(lid):
    return db_exec("SELECT * FROM reviews WHERE lesson_id=? ORDER BY id DESC", (lid,), "all")


def get_avg_rating(lid):
    r = db_exec("SELECT AVG(rating) AS a, COUNT(*) AS c FROM reviews WHERE lesson_id=?", (lid,), "one")
    return (round(r["a"], 1) if r["a"] else 0, r["c"])


def add_message(lid, username, message):
    db_exec("INSERT INTO messages (lesson_id, username, message) VALUES (?,?,?)",
            (lid, username, message), commit=True)


def get_messages(lid):
    return db_exec("SELECT * FROM messages WHERE lesson_id=? ORDER BY id DESC LIMIT 50", (lid,), "all")


# ════════════════════════════════════════════════════════════
#  البطاقات والملاحظات
# ════════════════════════════════════════════════════════════
def add_flashcard(u, subject, front, back):
    return db_exec(
        "INSERT INTO flashcards (username, subject, front, back) VALUES (?,?,?,?)",
        (u, subject, front, back), commit=True)


def get_flashcards(u, s=None):
    if s and s != "all":
        return db_exec("SELECT * FROM flashcards WHERE username=? AND subject=? ORDER BY id DESC",
                       (u, s), "all")
    return db_exec("SELECT * FROM flashcards WHERE username=? ORDER BY id DESC", (u,), "all")


def delete_flashcard(fid):
    db_exec("DELETE FROM flashcards WHERE id=?", (fid,), commit=True)


def toggle_flashcard_known(fid):
    db_exec("UPDATE flashcards SET known = 1 - known WHERE id=?", (fid,), commit=True)


def add_note(u, lid, note):
    return db_exec("INSERT INTO notes (username, lesson_id, note) VALUES (?,?,?)",
                   (u, lid, note), commit=True)


def get_notes(u, lid):
    return db_exec("SELECT * FROM notes WHERE username=? AND lesson_id=? ORDER BY id DESC",
                   (u, lid), "all")


def delete_note(nid):
    db_exec("DELETE FROM notes WHERE id=?", (nid,), commit=True)


# ════════════════════════════════════════════════════════════
#  الأصدقاء
# ════════════════════════════════════════════════════════════
def add_friend(u, fu):
    fu = (fu or "").strip()
    if not fu:
        return False, "أدخل اسم المستخدم"
    if fu == u:
        return False, "ما يمكنكش تضيف راسك"
    target = db_exec("SELECT username, role FROM users WHERE username=?", (fu,), "one")
    if not target or target["role"] != "student":
        return False, "هاد التلميذ غير موجود"
    if db_exec("SELECT id FROM friends WHERE username=? AND friend_username=?", (u, fu), "one"):
        return False, "هاد التلميذ صديقك من قبل"
    db_exec("INSERT INTO friends (username, friend_username, status) VALUES (?,?,?)",
            (u, fu, "accepted"), commit=True)
    add_notification(fu, "صديق جديد", f"{u} أضافك كصديق", "👥")
    return True, "تمت الإضافة"


def get_friends(u):
    rows = db_exec("SELECT friend_username FROM friends WHERE username=?", (u,), "all")
    out = []
    for r in rows:
        fu = r["friend_username"]
        usr = db_exec("SELECT full_name FROM users WHERE username=?", (fu,), "one") or {}
        st_ = get_user_stats(fu)
        out.append({
            "username": fu, "full_name": usr.get("full_name") or fu,
            "points": st_["total_points"], "level": st_["level"],
            "quizzes": st_["quizzes_taken"], "streak": st_["streak"],
        })
    out.sort(key=lambda x: x["points"], reverse=True)
    return out


def remove_friend(u, fu):
    db_exec("DELETE FROM friends WHERE username=? AND friend_username=?", (u, fu), commit=True)


# ════════════════════════════════════════════════════════════
#  خطة المراجعة
# ════════════════════════════════════════════════════════════
def add_study_plan(u, subject, priority, target_date):
    return db_exec(
        "INSERT INTO study_plan (username, subject, priority, target_date) VALUES (?,?,?,?)",
        (u, subject, priority, str(target_date)), commit=True)


def get_study_plan(u):
    return db_exec(
        "SELECT * FROM study_plan WHERE username=? ORDER BY completed, target_date", (u,), "all")


def toggle_study_plan(pid):
    db_exec("UPDATE study_plan SET completed = 1 - completed WHERE id=?", (pid,), commit=True)


def auto_generate_plan(u):
    stats = get_subject_stats(u)
    existing = {p["subject"] for p in get_study_plan(u) if not p["completed"]}
    added = 0
    for sub in SUBJECTS:
        if sub in existing:
            continue
        avg = stats.get(sub, {}).get("avg_percent")
        if avg is None:
            pr, days = "medium", 7
        elif avg < 60:
            pr, days = "high", 3
        elif avg < 80:
            pr, days = "medium", 7
        else:
            pr, days = "low", 14
        add_study_plan(u, sub, pr, date.today() + timedelta(days=days))
        added += 1
    return added


# ════════════════════════════════════════════════════════════
#  الثيم (CSS ديناميكي)
# ════════════════════════════════════════════════════════════
def apply_theme():
    th = THEMES.get(st.session_state.get("theme"), THEMES["🌙 Midnight Purple"])
    direction = "rtl" if st.session_state.get("lang", "ar") == "ar" else "ltr"
    align = "right" if direction == "rtl" else "left"
    css = f"""
    <style>
    @import url('https://fonts.googleapis.com/css2?family=Cairo:wght@400;600;700;800&display=swap');
    :root {{
        --bg:{th['bg']}; --card:{th['card']}; --text:{th['text']}; --accent:{th['accent']};
        --secondary:{th['secondary']}; --border:{th['border']}; --highlight:{th['highlight']};
    }}
    html, body, .stApp, [data-testid="stAppViewContainer"] {{
        background-color: var(--bg) !important;
        color: var(--text) !important;
        font-family: 'Cairo', sans-serif !important;
        direction: {direction};
    }}
    [data-testid="stHeader"] {{ background: transparent !important; }}
    [data-testid="stSidebar"] {{
        background-color: var(--secondary) !important;
        border-{ 'left' if direction == 'rtl' else 'right' }: 1px solid var(--border);
    }}
    .stApp p, .stApp label, .stApp li, .stApp h1, .stApp h2, .stApp h3, .stApp h4,
    .stApp h5, .stApp h6, .stApp span, .stApp div[data-testid="stMarkdownContainer"] {{
        color: var(--text) !important;
        text-align: {align};
        font-family: 'Cairo', sans-serif !important;
    }}
    .stApp h1, .stApp h2, .stApp h3 {{ color: var(--accent) !important; font-weight: 800; }}
    .stButton > button, .stDownloadButton > button, .stFormSubmitButton > button, .stLinkButton > a {{
        background: var(--card) !important;
        color: var(--text) !important;
        border: 1px solid var(--border) !important;
        border-radius: 12px !important;
        font-weight: 700 !important;
        transition: all .2s ease;
    }}
    .stButton > button:hover, .stFormSubmitButton > button:hover, .stDownloadButton > button:hover {{
        background: var(--accent) !important;
        border-color: var(--accent) !important;
        transform: translateY(-2px);
    }}
    .stButton > button[kind="primary"], .stFormSubmitButton > button[kind="primary"] {{
        background: var(--accent) !important;
        border-color: var(--accent) !important;
    }}
    .stTextInput input, .stTextArea textarea, .stNumberInput input, .stDateInput input,
    [data-baseweb="select"] > div, [data-baseweb="input"] {{
        background-color: var(--card) !important;
        color: var(--text) !important;
        border: 1px solid var(--border) !important;
        border-radius: 10px !important;
    }}
    [data-baseweb="popover"] ul, [data-baseweb="popover"] li, [data-baseweb="menu"] {{
        background-color: var(--card) !important;
        color: var(--text) !important;
    }}
    .stTabs [data-baseweb="tab-list"] {{ gap: 6px; }}
    .stTabs [data-baseweb="tab"] {{
        background: var(--card); border-radius: 10px 10px 0 0; padding: 8px 16px;
        border: 1px solid var(--border);
    }}
    .stTabs [aria-selected="true"] {{ background: var(--accent) !important; }}
    [data-testid="stExpander"] {{
        background: var(--card) !important;
        border: 1px solid var(--border) !important;
        border-radius: 14px !important;
    }}
    [data-testid="stMetric"] {{
        background: var(--card); border: 1px solid var(--border);
        border-radius: 14px; padding: 12px 16px;
    }}
    [data-testid="stMetricValue"] {{ color: var(--highlight) !important; }}
    .stProgress > div > div > div > div {{ background-color: var(--highlight) !important; }}
    [data-testid="stForm"] {{
        background: var(--card); border: 1px solid var(--border); border-radius: 14px; padding: 16px;
    }}
    .rm-card {{
        background: var(--card); border: 1px solid var(--border); border-radius: 16px;
        padding: 16px 20px; margin: 8px 0; box-shadow: 0 4px 14px rgba(0,0,0,.18);
    }}
    .rm-subject {{
        background: var(--card); border: 1px solid var(--border); border-radius: 16px;
        padding: 14px; text-align: center; margin-bottom: 6px;
    }}
    .rm-badge {{
        display:inline-block; background: var(--card); border:1px solid var(--highlight);
        color: var(--highlight) !important; border-radius: 20px; padding: 6px 14px; margin: 4px;
        font-weight: 700;
    }}
    .rm-badge-locked {{
        display:inline-block; background: var(--secondary); border:1px dashed var(--border);
        opacity: .5; border-radius: 20px; padding: 6px 14px; margin: 4px;
    }}
    .rm-timer {{
        background: var(--accent); color: #fff !important; border-radius: 12px;
        padding: 10px 18px; text-align:center; font-size: 1.4rem; font-weight: 800;
    }}
    .rm-footer {{
        text-align:center; opacity:.75; padding: 22px 0 8px 0; margin-top: 30px;
        border-top: 1px solid var(--border); font-size: .9rem;
    }}
    .rm-hero {{
        background: linear-gradient(135deg, var(--accent), var(--border));
        border-radius: 20px; padding: 28px; text-align:center; margin-bottom: 18px;
    }}
    .rm-hero h1, .rm-hero p {{ color: #fff !important; text-align:center !important; }}
    </style>
    """
    st.markdown(css, unsafe_allow_html=True)


def render_footer():
    st.markdown(f'<div class="rm-footer">{FOOTER_TEXT}</div>', unsafe_allow_html=True)


# ════════════════════════════════════════════════════════════
#  حالة الجلسة
# ════════════════════════════════════════════════════════════
def init_session():
    defaults = {
        "authenticated": False, "user": None, "role": None, "full_name": None,
        "page": "dashboard", "theme": "🌙 Midnight Purple", "lang": "ar",
        "auth_mode": "home", "quiz_lesson_id": None, "fc_idx": 0, "fc_flip": False,
        "qr_ids": None,
    }
    for k, v in defaults.items():
        if k not in st.session_state:
            st.session_state[k] = v


def go_page(p):
    st.session_state.page = p


def reset_quiz():
    for k in list(st.session_state.keys()):
        if k.startswith("quizans_"):
            del st.session_state[k]
    for k in ("quiz_start", "quiz_qids", "quiz_done", "quiz_result", "quiz_time_up"):
        st.session_state.pop(k, None)


def start_quiz(lid):
    reset_quiz()
    st.session_state.quiz_lesson_id = lid
    st.session_state.page = "quiz"


def set_auth_mode(m):
    st.session_state.auth_mode = m


def do_logout():
    reset_quiz()
    for k in list(st.session_state.keys()):
        if k not in ("theme", "lang"):
            del st.session_state[k]
    init_session()


# ════════════════════════════════════════════════════════════
#  صفحات الدخول
# ════════════════════════════════════════════════════════════
def render_auth_home():
    st.markdown(
        '<div class="rm-hero"><h1>📚 3AC RevisioMaroc</h1>'
        '<p>منصة المراجعة الذكية لتلاميذ الجذع المشترك</p></div>',
        unsafe_allow_html=True,
    )
    c1, c2, c3 = st.columns(3)
    with c1:
        st.markdown('<div class="rm-card"><h3>🎓 تلميذ</h3><p>دخول التلاميذ للمراجعة والاختبارات</p></div>',
                    unsafe_allow_html=True)
        st.button("دخول التلميذ", key="home_student", use_container_width=True,
                  on_click=set_auth_mode, args=("student",), type="primary")
    with c2:
        st.markdown('<div class="rm-card"><h3>🛠️ مطور</h3><p>إضافة الدروس والأسئلة وتدبير المحتوى</p></div>',
                    unsafe_allow_html=True)
        st.button("دخول المطور", key="home_dev", use_container_width=True,
                  on_click=set_auth_mode, args=("developer",))
    with c3:
        st.markdown('<div class="rm-card"><h3>✨ حساب جديد</h3><p>سجّل دابا وبدا المراجعة مجاناً</p></div>',
                    unsafe_allow_html=True)
        st.button("إنشاء حساب", key="home_reg", use_container_width=True,
                  on_click=set_auth_mode, args=("register",))


def _login_form(expected_role, title, key):
    st.markdown(f"## {title}")
    with st.form(f"login_{key}"):
        u = st.text_input(T("username"), key=f"{key}_u")
        p = st.text_input(T("password"), type="password", key=f"{key}_p")
        ok = st.form_submit_button(T("login"), type="primary", use_container_width=True)
    if ok:
        user = authenticate(u, p)
        if not user:
            st.error("❌ اسم المستخدم أو كلمة المرور غير صحيحة")
        elif user["role"] != expected_role:
            st.error("❌ هاد الحساب ما كيدخلش من هاد الصفحة، جرب الصفحة الأخرى")
        else:
            st.session_state.authenticated = True
            st.session_state.user = user["username"]
            st.session_state.role = user["role"]
            st.session_state.full_name = user["full_name"] or user["username"]
            st.session_state.page = "dev_panel" if user["role"] == "developer" else "dashboard"
            get_user_stats(user["username"])
            st.rerun()
    st.button(T("back"), key=f"back_{key}", on_click=set_auth_mode, args=("home",))


def render_student_login():
    _login_form("student", "🎓 دخول التلميذ", "student")


def render_developer_login():
    _login_form("developer", "🛠️ دخول المطور", "developer")


def render_register():
    st.markdown("## ✨ إنشاء حساب جديد")
    with st.form("register_form"):
        n = st.text_input(T("full_name"))
        u = st.text_input(T("username"))
        p = st.text_input(T("password"), type="password")
        p2 = st.text_input("تأكيد كلمة المرور", type="password")
        ok = st.form_submit_button(T("register"), type="primary", use_container_width=True)
    if ok:
        if p != p2:
            st.error("❌ كلمتا المرور غير متطابقتين")
        else:
            success, msg = register_user(u, p, n)
            if success:
                st.success("✅ " + msg + " — يمكنك الآن تسجيل الدخول")
                st.session_state.auth_mode = "student"
            else:
                st.error("❌ " + msg)
    st.button(T("back"), key="back_reg", on_click=set_auth_mode, args=("home",))


def render_auth_page():
    mode = st.session_state.get("auth_mode", "home")
    _, mid, _ = st.columns([1, 3, 1])
    with mid:
        if mode == "student":
            render_student_login()
        elif mode == "developer":
            render_developer_login()
        elif mode == "register":
            render_register()
        else:
            render_auth_home()
        render_footer()


# ════════════════════════════════════════════════════════════
#  لوحة التحكم
# ════════════════════════════════════════════════════════════
def render_dashboard():
    u = st.session_state.user
    s = get_user_stats(u)
    st.title(f"🏠 {T('welcome')} {st.session_state.full_name}")

    if can_claim_daily(u):
        st.info("🎁 عندك مكافأة يومية جاهزة!")
        if st.button("🎁 استلم المكافأة اليومية", key="claim_daily", type="primary"):
            ok, bonus, streak = check_daily_bonus(u)
            if ok:
                st.success(f"🎉 ربحتي {bonus} نقطة — التتابع: {streak} يوم")
                st.balloons()
                time.sleep(1)
                st.rerun()

    s = get_user_stats(u)
    c1, c2, c3, c4, c5 = st.columns(5)
    c1.metric("⭐ " + T("points"), s["total_points"])
    c2.metric("🆙 " + T("level"), s["level"])
    c3.metric("🎖️ " + T("rank"), get_rank(s["level"]))
    c4.metric("🔥 " + T("streak"), f"{s['streak']} يوم")
    c5.metric("📝 " + T("quizzes"), s["quizzes_taken"])

    in_level = s["total_points"] % 100
    st.markdown(f"**التقدم نحو المستوى {s['level'] + 1}** — {in_level}/100")
    st.progress(in_level / 100)

    weak = get_weaknesses(u)
    if weak:
        st.warning("⚠️ نقاط ضعف: " + "، ".join(
            f"{SUBJECTS[sb]['icon']} {SUBJECTS[sb]['name']} ({p:.0f}%)" for sb, p in weak if sb in SUBJECTS))

    st.markdown("### 📚 المواد")
    stats = get_subject_stats(u)
    cols = st.columns(4)
    for i, (key, info) in enumerate(SUBJECTS.items()):
        with cols[i % 4]:
            cnt = len(load_lessons(subject=key))
            avg = stats.get(key, {}).get("avg_percent")
            avg_txt = f"{avg:.0f}%" if avg is not None else "—"
            st.markdown(
                f'<div class="rm-subject" style="border-top:4px solid {info["color"]};">'
                f'<div style="font-size:2rem;">{info["icon"]}</div>'
                f'<b>{info["name"]}</b><br><small>{cnt} درس • المعدل {avg_txt}</small></div>',
                unsafe_allow_html=True,
            )

            def _open_subject(k=key):
                st.session_state["lessons_subject"] = k
                st.session_state.page = "lessons"
            st.button("فتح", key=f"dash_sub_{key}", use_container_width=True, on_click=_open_subject)

    hist = get_quiz_history(u, 5)
    if hist:
        st.markdown("### 🕒 آخر الاختبارات")
        for h in hist:
            sub = SUBJECTS.get(h["subject"], {"icon": "📘", "name": h["subject"]})
            st.markdown(
                f'<div class="rm-card">{sub["icon"]} <b>{h["lesson_title"]}</b> — '
                f'{h["score"]}/{h["total"]} ({h["percent"]:.0f}%) <small>• {h["created_at"]}</small></div>',
                unsafe_allow_html=True)
    render_footer()


# ════════════════════════════════════════════════════════════
#  الدروس
# ════════════════════════════════════════════════════════════
def render_lessons():
    st.title("📚 " + T("lessons"))
    keys = ["all"] + list(SUBJECTS.keys())
    default = st.session_state.get("lessons_subject", "all")
    if default not in keys:
        default = "all"
    c1, c2, c3 = st.columns([2, 2, 3])
    with c1:
        subject = st.selectbox(
            T("subject"), keys, index=keys.index(default),
            format_func=lambda k: T("all") if k == "all" else f"{SUBJECTS[k]['icon']} {SUBJECTS[k]['name']}",
            key="lessons_subject_sel")
    with c2:
        lang = st.selectbox("اللغة", ["all", "ar", "fr", "en"],
                            format_func=lambda k: T("all") if k == "all" else LESSON_LANGS[k],
                            key="lessons_lang_sel")
    with c3:
        search = st.text_input(T("search"), key="lessons_search")
    lessons = load_lessons(subject, lang, None, search or None)
    if not lessons:
        st.info("ما كاين حتى درس بهاد المعايير.")
    for l in lessons:
        _render_lesson_card(l)
    render_footer()


def _render_lesson_card(lesson):
    u = st.session_state.user
    lid = lesson["id"]
    sub = SUBJECTS.get(lesson["subject"], {"icon": "📘", "name": lesson["subject"], "color": "#888"})
    avg, cnt = get_avg_rating(lid)
    fav = "⭐ " if is_favorite(u, lid) else ""
    rating_txt = f" • ⭐ {avg} ({cnt})" if cnt else ""
    with st.expander(f"{fav}{sub['icon']} {lesson['title']} — {sub['name']}{rating_txt}"):
        tabs = st.tabs(["📖 الدرس", "⭐ التقييمات", "💬 النقاش", "📝 ملاحظاتي"])
        with tabs[0]:
            st.caption(f"اللغة: {LESSON_LANGS.get(lesson['language'], lesson['language'])} • "
                       f"الناشر: {lesson['owner']} • {lesson['created_at']}")
            if lesson["image_url"]:
                try:
                    st.image(lesson["image_url"], use_container_width=True)
                except Exception:
                    st.warning("تعذر عرض الصورة")
            if lesson["content"]:
                st.markdown(lesson["content"])
            if lesson["pdf_url"]:
                st.markdown("#### 📄 ملف PDF")
                render_pdf(lesson["pdf_url"], key=f"lesson_{lid}")
            b1, b2 = st.columns(2)
            with b1:
                label = "💔 إزالة من المفضلة" if is_favorite(u, lid) else "⭐ أضف للمفضلة"
                if st.button(label, key=f"fav_{lid}", use_container_width=True):
                    toggle_favorite(u, lid)
                    st.rerun()
            with b2:
                nq = len(load_questions(lid))
                st.button(f"📝 ابدأ الاختبار ({nq} سؤال)", key=f"startq_{lid}", use_container_width=True,
                          disabled=nq == 0, on_click=start_quiz, args=(lid,), type="primary")
        with tabs[1]:
            _render_reviews(lid)
        with tabs[2]:
            _render_discussion(lid)
        with tabs[3]:
            _render_notes(lid)


def _render_reviews(lid):
    u = st.session_state.user
    avg, cnt = get_avg_rating(lid)
    st.markdown(f"**التقييم العام:** {'⭐' * int(round(avg))} {avg}/5 ({cnt} تقييم)")
    with st.form(f"review_form_{lid}", clear_on_submit=True):
        rating = st.slider("تقييمك", 1, 5, 5, key=f"rate_{lid}")
        comment = st.text_area("تعليقك", key=f"rcom_{lid}")
        if st.form_submit_button("إرسال التقييم"):
            add_review(lid, u, rating, comment)
            st.success("شكراً على تقييمك!")
            st.rerun()
    for r in get_reviews(lid):
        st.markdown(
            f'<div class="rm-card"><b>{r["username"]}</b> — {"⭐" * r["rating"]}<br>{r["comment"] or ""}</div>',
            unsafe_allow_html=True)


def _render_discussion(lid):
    u = st.session_state.user
    with st.form(f"disc_form_{lid}", clear_on_submit=True):
        msg = st.text_area("اكتب رسالة أو سؤال", key=f"dmsg_{lid}")
        if st.form_submit_button("إرسال"):
            if msg.strip():
                add_message(lid, u, msg.strip())
                st.rerun()
            else:
                st.warning("الرسالة فارغة")
    msgs = get_messages(lid)
    if not msgs:
        st.caption("ما كاين حتى رسالة، كون أول واحد!")
    for m in msgs:
        st.markdown(f'<div class="rm-card"><b>💬 {m["username"]}</b><br>{m["message"]}</div>',
                    unsafe_allow_html=True)


def _render_notes(lid):
    u = st.session_state.user
    with st.form(f"note_form_{lid}", clear_on_submit=True):
        note = st.text_area("ملاحظة جديدة", key=f"nnote_{lid}")
        if st.form_submit_button("💾 حفظ"):
            if note.strip():
                add_note(u, lid, note.strip())
                st.rerun()
            else:
                st.warning("الملاحظة فارغة")
    for n in get_notes(u, lid):
        c1, c2 = st.columns([8, 1])
        with c1:
            st.markdown(f'<div class="rm-card">📝 {n["note"]}</div>', unsafe_allow_html=True)
        with c2:
            if st.button("🗑️", key=f"delnote_{n['id']}"):
                delete_note(n["id"])
                st.rerun()


# ════════════════════════════════════════════════════════════
#  الاختبار
# ════════════════════════════════════════════════════════════
def render_quiz():
    st.title("📝 " + T("quiz"))
    lid = st.session_state.get("quiz_lesson_id")
    if not lid:
        lessons = [l for l in load_lessons() if load_questions(l["id"])]
        if not lessons:
            st.info("ما كاين حتى درس فيه أسئلة دابا.")
            render_footer()
            return
        opts = {l["id"]: f"{SUBJECTS.get(l['subject'], {}).get('icon', '📘')} {l['title']}" for l in lessons}
        choice = st.selectbox("اختر الدرس", list(opts.keys()), format_func=lambda k: opts[k], key="quiz_pick")
        st.button(T("start_quiz"), key="quiz_begin", on_click=start_quiz, args=(choice,), type="primary")
        render_footer()
        return

    lesson = get_lesson(lid)
    questions = load_questions(lid)
    if not lesson or not questions:
        st.warning("هاد الدرس ما فيهش أسئلة.")
        st.button("اختيار درس آخر", on_click=lambda: (reset_quiz(), st.session_state.update(quiz_lesson_id=None)))
        render_footer()
        return
    st.subheader(f"{SUBJECTS.get(lesson['subject'], {}).get('icon', '')} {lesson['title']}")
    _render_quiz_ui(questions, lid)
    render_footer()


def _time_left():
    start = st.session_state.get("quiz_start")
    if not start:
        return QUIZ_DURATION
    return max(0, int(QUIZ_DURATION - (time.time() - start)))


def _timer_body():
    left = _time_left()
    m, s = divmod(left, 60)
    st.markdown(f'<div class="rm-timer">⏱️ {m:02d}:{s:02d}</div>', unsafe_allow_html=True)
    st.progress(left / QUIZ_DURATION)
    if left <= 0 and not st.session_state.get("quiz_done"):
        st.session_state.quiz_time_up = True
        st.rerun()


try:
    _timer_fragment = st.fragment(run_every=1)(_timer_body)
except Exception:
    _timer_fragment = _timer_body


def _grade_quiz(ordered, lesson):
    ss = st.session_state
    u = ss.user
    score = 0
    details = []
    for q in ordered:
        ans = ss.get(f"quizans_{q['id']}")
        ok = ans == q["correct_answer"]
        if ok:
            score += 1
        details.append({"q": q, "ans": ans, "ok": ok})
    total = len(ordered)
    points = score * 10
    percent = save_quiz_result(u, lesson["id"], lesson["title"], lesson["subject"], score, total)
    update_user_stats(u, points, 1, 1 if (score == total and total > 0) else 0, lesson["subject"])
    ss.quiz_result = {"score": score, "total": total, "points": points, "percent": percent,
                      "details": details, "timeout": bool(ss.get("quiz_time_up"))}
    ss.quiz_done = True
    ss.pop("quiz_time_up", None)
    st.rerun()


def _render_quiz_ui(questions, lesson_id):
    ss = st.session_state
    lesson = get_lesson(lesson_id)

    if ss.get("quiz_done"):
        _show_quiz_result()
        return

    if "quiz_qids" not in ss:
        ids = [q["id"] for q in questions]
        random.shuffle(ids)
        ss.quiz_qids = ids
        ss.quiz_start = time.time()

    qmap = {q["id"]: q for q in questions}
    ordered = [qmap[i] for i in ss.quiz_qids if i in qmap]

    if _time_left() <= 0:
        ss.quiz_time_up = True
        _grade_quiz(ordered, lesson)
        return

    _timer_fragment()
    st.markdown(f"**عدد الأسئلة:** {len(ordered)} • **كل جواب صحيح = 10 نقاط**")

    for i, q in enumerate(ordered, 1):
        st.markdown(f'<div class="rm-card"><b>السؤال {i}:</b> {q["question"]}</div>', unsafe_allow_html=True)
        opts = {k: q[f"option_{k.lower()}"] for k in "ABCD" if q.get(f"option_{k.lower()}")}
        st.radio(
            f"اختيارات السؤال {i}", list(opts.keys()),
            format_func=lambda k, o=opts: f"{k}) {o[k]}",
            index=None, key=f"quizans_{q['id']}", label_visibility="collapsed",
        )

    c1, c2 = st.columns(2)
    with c1:
        if st.button(T("submit"), key="quiz_submit", type="primary", use_container_width=True):
            _grade_quiz(ordered, lesson)
    with c2:
        st.button("❌ إلغاء", key="quiz_cancel", use_container_width=True,
                  on_click=lambda: (reset_quiz(), st.session_state.update(quiz_lesson_id=None)))


def _show_quiz_result():
    ss = st.session_state
    res = ss.quiz_result
    if res.get("timeout"):
        st.error("⏰ سالا الوقت! تم تسليم الاختبار أوتوماتيكياً.")
    pct = res["percent"]
    if pct == 100:
        st.balloons()
        st.success("💯 ممتاز! العلامة الكاملة!")
    elif pct >= 70:
        st.success("👏 نتيجة مزيانة، كمل هاد المجهود!")
    elif pct >= 50:
        st.warning("🙂 نتيجة متوسطة، راجع الدرس مرة أخرى.")
    else:
        st.error("📖 خاصك تراجع الدرس مزيان وتعاود.")
    c1, c2, c3 = st.columns(3)
    c1.metric("النتيجة", f"{res['score']}/{res['total']}")
    c2.metric("النسبة", f"{pct:.0f}%")
    c3.metric("نقاط مكتسبة", f"+{res['points']}")

    st.markdown("### 🔍 التصحيح")
    for i, d in enumerate(res["details"], 1):
        q = d["q"]
        icon = "✅" if d["ok"] else "❌"
        your = d["ans"] or "—"
        correct_txt = q.get(f"option_{q['correct_answer'].lower()}", "")
        st.markdown(
            f'<div class="rm-card">{icon} <b>السؤال {i}:</b> {q["question"]}<br>'
            f'جوابك: <b>{your}</b> • الجواب الصحيح: <b>{q["correct_answer"]}) {correct_txt}</b>'
            f'{"<br>💡 " + q["explanation"] if q["explanation"] else ""}</div>',
            unsafe_allow_html=True)
    c1, c2 = st.columns(2)
    with c1:
        lid = ss.quiz_lesson_id
        st.button("🔄 إعادة الاختبار", key="quiz_retry", use_container_width=True,
                  on_click=start_quiz, args=(lid,), type="primary")
    with c2:
        st.button("📚 اختبار آخر", key="quiz_other", use_container_width=True,
                  on_click=lambda: (reset_quiz(), st.session_state.update(quiz_lesson_id=None)))


# ════════════════════════════════════════════════════════════
#  مراجعة سريعة
# ════════════════════════════════════════════════════════════
def _new_quick_set(subject):
    sql = "SELECT q.id FROM questions q JOIN lessons l ON l.id=q.lesson_id"
    params = ()
    if subject != "all":
        sql += " WHERE l.subject=?"
        params = (subject,)
    ids = [r["id"] for r in db_exec(sql, params, "all")]
    random.shuffle(ids)
    st.session_state.qr_ids = ids[:5]
    for k in list(st.session_state.keys()):
        if k.startswith("qrans_") or k.startswith("qrshow_"):
            del st.session_state[k]


def render_quick_review():
    st.title("⚡ " + T("quick_review"))
    st.caption("5 أسئلة عشوائية للمراجعة السريعة — بدون مؤقت وبدون نقاط.")
    keys = ["all"] + list(SUBJECTS.keys())
    subject = st.selectbox(
        T("subject"), keys,
        format_func=lambda k: T("all") if k == "all" else f"{SUBJECTS[k]['icon']} {SUBJECTS[k]['name']}",
        key="qr_subject")
    st.button("🎲 مجموعة جديدة", key="qr_new", on_click=_new_quick_set, args=(subject,), type="primary")
    ids = st.session_state.get("qr_ids")
    if ids is None:
        st.info("اضغط على «مجموعة جديدة» باش تبدا.")
    elif not ids:
        st.warning("ما كاين حتى سؤال فهاد المادة.")
    else:
        for i, qid in enumerate(ids, 1):
            q = db_exec("SELECT * FROM questions WHERE id=?", (qid,), "one")
            if not q:
                continue
            st.markdown(f'<div class="rm-card"><b>{i}.</b> {q["question"]}</div>', unsafe_allow_html=True)
            opts = {k: q[f"option_{k.lower()}"] for k in "ABCD" if q.get(f"option_{k.lower()}")}
            ans = st.radio(f"qr{i}", list(opts.keys()), format_func=lambda k, o=opts: f"{k}) {o[k]}",
                           index=None, key=f"qrans_{qid}", label_visibility="collapsed")
            if st.checkbox("👁️ أظهر الجواب", key=f"qrshow_{qid}"):
                if ans is None:
                    st.info(f"الجواب الصحيح: {q['correct_answer']}) {q['option_' + q['correct_answer'].lower()]}")
                elif ans == q["correct_answer"]:
                    st.success("✅ صحيح!")
                else:
                    st.error(f"❌ خطأ — الصحيح: {q['correct_answer']}) {q['option_' + q['correct_answer'].lower()]}")
                if q["explanation"]:
                    st.caption("💡 " + q["explanation"])
    render_footer()


# ════════════════════════════════════════════════════════════
#  البطاقات
# ════════════════════════════════════════════════════════════
def render_flashcards():
    u = st.session_state.user
    st.title("🃏 " + T("flashcards"))
    tab1, tab2, tab3 = st.tabs(["🎴 مراجعة", "➕ إضافة بطاقة", "📋 كل البطاقات"])
    keys = ["all"] + list(SUBJECTS.keys())

    with tab2:
        with st.form("fc_add", clear_on_submit=True):
            sub = st.selectbox(T("subject"), list(SUBJECTS.keys()),
                               format_func=lambda k: f"{SUBJECTS[k]['icon']} {SUBJECTS[k]['name']}")
            front = st.text_area("الوجه الأمامي (السؤال / المصطلح)")
            back = st.text_area("الوجه الخلفي (الجواب / التعريف)")
            if st.form_submit_button("💾 حفظ البطاقة", type="primary"):
                if front.strip() and back.strip():
                    add_flashcard(u, sub, front.strip(), back.strip())
                    st.success("تمت إضافة البطاقة")
                else:
                    st.warning("عمّر الوجهين")

    with tab1:
        fsub = st.selectbox(
            T("subject"), keys,
            format_func=lambda k: T("all") if k == "all" else f"{SUBJECTS[k]['icon']} {SUBJECTS[k]['name']}",
            key="fc_filter")
        only_unknown = st.checkbox("غير المحفوظة فقط", value=True, key="fc_unknown")
        cards = get_flashcards(u, fsub)
        if only_unknown:
            cards = [c for c in cards if not c["known"]]
        if not cards:
            st.info("ما كاين حتى بطاقة للمراجعة.")
        else:
            idx = st.session_state.fc_idx % len(cards)
            card = cards[idx]
            sub = SUBJECTS.get(card["subject"], {"icon": "📘", "name": ""})
            st.caption(f"البطاقة {idx + 1}/{len(cards)} • {sub['icon']} {sub['name']}")
            text = card["back"] if st.session_state.fc_flip else card["front"]
            label = "الجواب" if st.session_state.fc_flip else "السؤال"
            st.markdown(
                f'<div class="rm-card" style="min-height:160px;text-align:center;font-size:1.3rem;">'
                f'<small>{label}</small><br><br>{text}</div>', unsafe_allow_html=True)
            c1, c2, c3, c4 = st.columns(4)

            def _flip():
                st.session_state.fc_flip = not st.session_state.fc_flip

            def _next(step):
                st.session_state.fc_idx += step
                st.session_state.fc_flip = False
            c1.button("🔄 قلب", key="fc_flipbtn", on_click=_flip, use_container_width=True)
            c2.button("⏮️ السابقة", key="fc_prev", on_click=_next, args=(-1,), use_container_width=True)
            c3.button("⏭️ التالية", key="fc_next", on_click=_next, args=(1,), use_container_width=True)
            if c4.button("✅ حفظتها", key="fc_known", use_container_width=True, type="primary"):
                toggle_flashcard_known(card["id"])
                st.session_state.fc_flip = False
                st.rerun()

    with tab3:
        allc = get_flashcards(u)
        if not allc:
            st.info("ما عندك حتى بطاقة.")
        known = sum(1 for c in allc if c["known"])
        if allc:
            st.markdown(f"**المحفوظة:** {known}/{len(allc)}")
            st.progress(known / len(allc))
        for c in allc:
            sub = SUBJECTS.get(c["subject"], {"icon": "📘", "name": ""})
            c1, c2, c3 = st.columns([8, 1, 1])
            with c1:
                st.markdown(
                    f'<div class="rm-card">{"✅" if c["known"] else "🔸"} {sub["icon"]} '
                    f'<b>{c["front"]}</b><br><small>{c["back"]}</small></div>', unsafe_allow_html=True)
            with c2:
                if st.button("🔁", key=f"fc_t_{c['id']}", help="تبديل الحالة"):
                    toggle_flashcard_known(c["id"])
                    st.rerun()
            with c3:
                if st.button("🗑️", key=f"fc_d_{c['id']}"):
                    delete_flashcard(c["id"])
                    st.rerun()
    render_footer()


# ════════════════════════════════════════════════════════════
#  خطة المراجعة
# ════════════════════════════════════════════════════════════
def render_study_plan():
    u = st.session_state.user
    st.title("🗓️ " + T("study_plan"))
    c1, c2 = st.columns([3, 1])
    with c2:
        if st.button("🤖 توليد خطة تلقائية", key="plan_auto", type="primary", use_container_width=True):
            n = auto_generate_plan(u)
            st.success(f"تمت إضافة {n} مهمة" if n else "الخطة كاملة من قبل")
            st.rerun()
    with st.expander("➕ إضافة مهمة"):
        with st.form("plan_add", clear_on_submit=True):
            sub = st.selectbox(T("subject"), list(SUBJECTS.keys()),
                               format_func=lambda k: f"{SUBJECTS[k]['icon']} {SUBJECTS[k]['name']}")
            pr = st.selectbox("الأولوية", list(PRIORITIES.keys()), format_func=lambda k: PRIORITIES[k])
            td = st.date_input("التاريخ المستهدف", value=date.today() + timedelta(days=7))
            if st.form_submit_button("إضافة"):
                add_study_plan(u, sub, pr, td)
                st.rerun()
    plan = get_study_plan(u)
    if not plan:
        st.info("ما عندك حتى مهمة. جرب التوليد التلقائي.")
    else:
        done = sum(1 for p in plan if p["completed"])
        st.markdown(f"**الإنجاز:** {done}/{len(plan)}")
        st.progress(done / len(plan))
    for p in plan:
        sub = SUBJECTS.get(p["subject"], {"icon": "📘", "name": p["subject"]})
        late = (not p["completed"]) and p["target_date"] < date.today().isoformat()
        c1, c2 = st.columns([1, 9])
        with c1:
            checked = st.checkbox("تم", value=bool(p["completed"]), key=f"plan_{p['id']}",
                                  label_visibility="collapsed")
            if checked != bool(p["completed"]):
                toggle_study_plan(p["id"])
                st.rerun()
        with c2:
            style = "text-decoration:line-through;opacity:.6;" if p["completed"] else ""
            st.markdown(
                f'<div class="rm-card" style="{style}">{sub["icon"]} <b>{sub["name"]}</b> • '
                f'{PRIORITIES.get(p["priority"], p["priority"])} • 📅 {p["target_date"]}'
                f'{" ⚠️ متأخرة" if late else ""}</div>', unsafe_allow_html=True)
    render_footer()


# ════════════════════════════════════════════════════════════
#  الأصدقاء
# ════════════════════════════════════════════════════════════
def render_friends():
    u = st.session_state.user
    st.title("👥 " + T("friends"))
    with st.form("friend_add", clear_on_submit=True):
        fu = st.text_input("اسم مستخدم صديقك")
        if st.form_submit_button("➕ إضافة صديق", type="primary"):
            ok, msg = add_friend(u, fu)
            (st.success if ok else st.error)(msg)
    friends = get_friends(u)
    me = get_user_stats(u)
    if not friends:
        st.info("ما عندك حتى صديق بعد.")
    else:
        st.markdown(f"**نقاطك:** ⭐ {me['total_points']}")
        for i, f in enumerate(friends, 1):
            c1, c2 = st.columns([9, 1])
            diff = f["points"] - me["total_points"]
            cmp_txt = f"أمامك بـ {diff}" if diff > 0 else (f"وراءك بـ {-diff}" if diff < 0 else "متعادلين")
            with c1:
                st.markdown(
                    f'<div class="rm-card"><b>{i}. {f["full_name"]}</b> (@{f["username"]})<br>'
                    f'⭐ {f["points"]} • 🆙 {f["level"]} • {get_rank(f["level"])} • '
                    f'📝 {f["quizzes"]} • 🔥 {f["streak"]} — <i>{cmp_txt}</i></div>',
                    unsafe_allow_html=True)
            with c2:
                if st.button("🗑️", key=f"rmf_{f['username']}"):
                    remove_friend(u, f["username"])
                    st.rerun()
    render_footer()


# ════════════════════════════════════════════════════════════
#  الترتيب
# ════════════════════════════════════════════════════════════
def render_leaderboard():
    st.title("🏆 " + T("leaderboard"))
    period = st.radio("الفترة", ["all", "month", "week"], horizontal=True,
                      format_func=lambda k: {"all": "🌍 دائماً", "month": "📅 الشهر", "week": "🗓️ الأسبوع"}[k],
                      key="lb_period")
    rows = get_leaderboard(period)
    if not rows:
        st.info("ما كاين حتى نتيجة فهاد الفترة.")
    medals = {1: "🥇", 2: "🥈", 3: "🥉"}
    me = st.session_state.user
    for i, r in enumerate(rows, 1):
        mark = " ← أنت" if r["username"] == me else ""
        lvl = f" • 🆙 {r['level']}" if r.get("level") else ""
        border = "2px solid var(--highlight)" if r["username"] == me else "1px solid var(--border)"
        st.markdown(
            f'<div class="rm-card" style="border:{border};"><b>{medals.get(i, i)} {r["full_name"]}</b> '
            f'(@{r["username"]}){mark}<br>⭐ {r["points"]} نقطة{lvl} • 📝 {r["quizzes"]} اختبار</div>',
            unsafe_allow_html=True)
    render_footer()


# ════════════════════════════════════════════════════════════
#  التقرير الأسبوعي
# ════════════════════════════════════════════════════════════
def render_weekly_report():
    u = st.session_state.user
    st.title("📈 " + T("weekly_report"))
    rep = get_weekly_report(u)
    c1, c2, c3, c4 = st.columns(4)
    c1.metric("📝 اختبارات", rep["count"])
    c2.metric("📊 المعدل", f"{rep['avg']}%")
    c3.metric("⭐ نقاط", rep["points"])
    c4.metric("✅ أجوبة صحيحة", f"{rep['correct']}/{rep['questions']}")
    if rep["count"] == 0:
        st.info("ما درتي حتى اختبار هاد الأسبوع. يالله نبداو! 💪")
    else:
        if rep["avg"] >= 80:
            st.success("🌟 أسبوع رائع، كمل هكا!")
        elif rep["avg"] >= 60:
            st.info("👍 أسبوع مزيان، تقدر تتحسن أكثر.")
        else:
            st.warning("📖 خاصك تركز أكثر هاد الأسبوع الجاي.")
        st.markdown("### 📚 الأداء حسب المادة")
        for r in rep["by_subject"]:
            sub = SUBJECTS.get(r["subject"], {"icon": "📘", "name": r["subject"]})
            st.markdown(f"{sub['icon']} **{sub['name']}** — {r['avg_percent']:.0f}% ({r['cnt']} اختبار)")
            st.progress(min(1.0, (r["avg_percent"] or 0) / 100))
        st.markdown("### 🕒 سجل الأسبوع")
        st.dataframe(
            [{"الدرس": h["lesson_title"], "المادة": SUBJECTS.get(h["subject"], {}).get("name", h["subject"]),
              "النتيجة": f"{h['score']}/{h['total']}", "النسبة": f"{h['percent']:.0f}%",
              "التاريخ": h["created_at"]} for h in rep["history"]],
            use_container_width=True, hide_index=True)
    weak = get_weaknesses(u)
    if weak:
        st.markdown("### ⚠️ مواد خاصك تقوّيها")
        for sb, p in weak:
            if sb in SUBJECTS:
                st.markdown(f"- {SUBJECTS[sb]['icon']} {SUBJECTS[sb]['name']} — {p:.0f}%")
    render_footer()


# ════════════════════════════════════════════════════════════
#  الإشعارات
# ════════════════════════════════════════════════════════════
def render_notifications():
    u = st.session_state.user
    st.title("🔔 " + T("notifications"))
    notes = get_notifications(u)
    unread = [n for n in notes if not n["is_read"]]
    if unread:
        if st.button("✔️ تعليم الكل كمقروء", key="notif_read", type="primary"):
            mark_notifications_read(u)
            st.rerun()
    if not notes:
        st.info("ما عندك حتى إشعار.")
    for n in notes:
        weight = "border:2px solid var(--highlight);" if not n["is_read"] else ""
        st.markdown(
            f'<div class="rm-card" style="{weight}">{n["icon"]} <b>{n["title"]}</b><br>{n["message"]}</div>',
            unsafe_allow_html=True)
    render_footer()


# ════════════════════════════════════════════════════════════
#  إحصائياتي
# ════════════════════════════════════════════════════════════
def render_my_stats():
    u = st.session_state.user
    st.title("📊 " + T("my_stats"))
    s = get_user_stats(u)
    c1, c2, c3, c4 = st.columns(4)
    c1.metric("⭐ النقاط", s["total_points"])
    c2.metric("🆙 المستوى", s["level"])
    c3.metric("🎖️ اللقب", get_rank(s["level"]))
    c4.metric("🔥 التتابع", f"{s['streak']} يوم")
    c1, c2, c3 = st.columns(3)
    c1.metric("📝 اختبارات", s["quizzes_taken"])
    c2.metric("💯 علامات كاملة", s["perfect_scores"])
    c3.metric("📚 مواد مختلفة", f"{len(s['subjects_list'])}/{len(SUBJECTS)}")

    st.markdown("### 🏅 الإنجازات")
    have = set(s["badges_list"])
    html = ""
    for k, name in BADGES.items():
        html += f'<span class="rm-badge">{name}</span>' if k in have else f'<span class="rm-badge-locked">🔒 {name}</span>'
    st.markdown(html, unsafe_allow_html=True)
    st.caption(f"{len(have)}/{len(BADGES)} شارة")

    st.markdown("### 📚 الأداء حسب المادة")
    stats = get_subject_stats(u)
    if not stats:
        st.info("ما درتي حتى اختبار بعد.")
    for key, d in stats.items():
        sub = SUBJECTS.get(key, {"icon": "📘", "name": key})
        st.markdown(f"{sub['icon']} **{sub['name']}** — المعدل {d['avg_percent']:.0f}% • "
                    f"أحسن نتيجة {d['best']:.0f}% • {d['cnt']} اختبار")
        st.progress(min(1.0, (d["avg_percent"] or 0) / 100))

    hist = get_quiz_history(u, 20)
    if hist:
        st.markdown("### 🕒 سجل الاختبارات")
        st.dataframe(
            [{"الدرس": h["lesson_title"], "المادة": SUBJECTS.get(h["subject"], {}).get("name", h["subject"]),
              "النتيجة": f"{h['score']}/{h['total']}", "النسبة": f"{h['percent']:.0f}%",
              "التاريخ": h["created_at"]} for h in hist],
            use_container_width=True, hide_index=True)
    render_footer()


# ════════════════════════════════════════════════════════════
#  المفضلة
# ════════════════════════════════════════════════════════════
def render_favorites():
    u = st.session_state.user
    st.title("⭐ " + T("favorites"))
    favs = get_favorites(u)
    if not favs:
        st.info("ما عندك حتى درس فالمفضلة.")
    for l in favs:
        _render_lesson_card(l)
    render_footer()


# ════════════════════════════════════════════════════════════
#  لوحة المطور
# ════════════════════════════════════════════════════════════
def render_developer_panel():
    if st.session_state.role != "developer":
        st.error("⛔ هاد الصفحة خاصة بالمطور فقط")
        render_footer()
        return
    u = st.session_state.user
    st.title("🛠️ " + T("dev_panel"))
    tab1, tab2, tab3, tab4 = st.tabs(["📚 إضافة درس", "❓ إضافة سؤال", "🗂️ تدبير المحتوى", "👥 المستخدمون"])

    with tab1:
        with st.form("dev_lesson", clear_on_submit=True):
            c1, c2 = st.columns(2)
            with c1:
                subject = st.selectbox(T("subject"), list(SUBJECTS.keys()),
                                       format_func=lambda k: f"{SUBJECTS[k]['icon']} {SUBJECTS[k]['name']}")
            with c2:
                language = st.selectbox("لغة الدرس", list(LESSON_LANGS.keys()),
                                        format_func=lambda k: LESSON_LANGS[k])
            title = st.text_input("عنوان الدرس")
            content = st.text_area("محتوى الدرس (يدعم Markdown)", height=250)
            img_url = st.text_input("رابط صورة (اختياري)")
            img_file = st.file_uploader("أو ارفع صورة", type=["png", "jpg", "jpeg", "webp"], key="dev_img")
            pdf_url = st.text_input("رابط PDF (اختياري)")
            pdf_file = st.file_uploader("أو ارفع ملف PDF", type=["pdf"], key="dev_pdf")
            if st.form_submit_button("💾 نشر الدرس", type="primary"):
                if not title.strip():
                    st.error("العنوان مطلوب")
                else:
                    img = upload_file(img_file, "images") if img_file else img_url.strip()
                    pdf = upload_file(pdf_file, "pdfs") if pdf_file else pdf_url.strip()
                    add_lesson(subject, language, title.strip(), content, img, pdf, u)
                    st.success("✅ تم نشر الدرس")

    with tab2:
        my_lessons = load_lessons(owner=u)
        if not my_lessons:
            st.info("زيد درس أولاً.")
        else:
            with st.form("dev_question", clear_on_submit=True):
                lid = st.selectbox("الدرس", [l["id"] for l in my_lessons],
                                   format_func=lambda k: next(l["title"] for l in my_lessons if l["id"] == k))
                question = st.text_area("السؤال")
                c1, c2 = st.columns(2)
                a = c1.text_input("الاختيار A")
                b = c2.text_input("الاختيار B")
                c = c1.text_input("الاختيار C")
                d = c2.text_input("الاختيار D")
                correct = st.selectbox("الجواب الصحيح", ["A", "B", "C", "D"])
                expl = st.text_area("شرح الجواب (اختياري)")
                if st.form_submit_button("➕ إضافة السؤال", type="primary"):
                    if not question.strip() or not a.strip() or not b.strip():
                        st.error("السؤال والاختيارين A و B على الأقل مطلوبين")
                    elif not {"A": a, "B": b, "C": c, "D": d}[correct].strip():
                        st.error("الجواب الصحيح لازم يكون اختيار معمّر")
                    else:
                        add_question(lid, question.strip(), a.strip(), b.strip(), c.strip(), d.strip(),
                                     correct, expl.strip())
                        st.success("✅ تمت إضافة السؤال")

    with tab3:
        my_lessons = load_lessons(owner=u)
        if not my_lessons:
            st.info("ما عندك حتى درس.")
        for l in my_lessons:
            sub = SUBJECTS.get(l["subject"], {"icon": "📘", "name": l["subject"]})
            qs = load_questions(l["id"])
            with st.expander(f"{sub['icon']} {l['title']} — {len(qs)} سؤال"):
                for q in qs:
                    c1, c2 = st.columns([9, 1])
                    with c1:
                        st.markdown(f"**{q['question']}**  \nA) {q['option_a']} | B) {q['option_b']} | "
                                    f"C) {q['option_c']} | D) {q['option_d']}  \n✅ {q['correct_answer']}")
                    with c2:
                        if st.button("🗑️", key=f"dq_{q['id']}"):
                            delete_question(q["id"])
                            st.rerun()
                if st.button("🗑️ حذف الدرس كاملاً", key=f"dl_{l['id']}"):
                    delete_lesson(l["id"], u)
                    st.rerun()

    with tab4:
        users = db_exec("SELECT username, full_name, role, created_at FROM users ORDER BY id DESC", (), "all")
        st.markdown(f"**عدد المستخدمين:** {len(users)}")
        st.dataframe(users, use_container_width=True, hide_index=True)
    render_footer()


# ════════════════════════════════════════════════════════════
#  الشريط الجانبي
# ════════════════════════════════════════════════════════════
def render_sidebar():
    u = st.session_state.user
    with st.sidebar:
        st.markdown(f"## 📚 {T('app_name')}")
        s = get_user_stats(u)
        st.markdown(
            f'<div class="rm-card"><b>👤 {st.session_state.full_name}</b><br>'
            f'<small>@{u} • {"🛠️ مطور" if st.session_state.role == "developer" else "🎓 تلميذ"}</small><br>'
            f'⭐ {s["total_points"]} • 🆙 {s["level"]}<br>{get_rank(s["level"])}</div>',
            unsafe_allow_html=True)

        theme_names = list(THEMES.keys())
        cur = st.session_state.theme if st.session_state.theme in theme_names else theme_names[4]
        new_theme = st.selectbox(T("theme"), theme_names, index=theme_names.index(cur), key="theme_sel")
        if new_theme != st.session_state.theme:
            st.session_state.theme = new_theme
            st.rerun()

        lang_keys = list(LANGS.keys())
        new_lang = st.selectbox(T("language"), lang_keys, index=lang_keys.index(st.session_state.lang),
                                format_func=lambda k: LANGS[k], key="lang_sel")
        if new_lang != st.session_state.lang:
            st.session_state.lang = new_lang
            st.rerun()

        st.markdown(f"### {T('menu')}")
        pages = list(PAGES)
        if st.session_state.role == "developer":
            pages.append("dev_panel")
        unread = len(get_notifications(u, unread=True))
        for p in pages:
            label = f"{PAGE_ICONS[p]} {T(p)}"
            if p == "notifications" and unread:
                label += f" ({unread})"
            st.button(label, key=f"nav_{p}", use_container_width=True,
                      type="primary" if st.session_state.page == p else "secondary",
                      on_click=go_page, args=(p,))

        st.divider()
        st.button(T("logout"), key="logout_btn", use_container_width=True, on_click=do_logout)
        st.markdown(f'<div class="rm-footer" style="font-size:.75rem;">{FOOTER_TEXT}</div>',
                    unsafe_allow_html=True)


# ════════════════════════════════════════════════════════════
#  التشغيل الرئيسي
# ════════════════════════════════════════════════════════════
init_session()
init_db()
apply_theme()

if not st.session_state.authenticated:
    render_auth_page()
    st.stop()

render_sidebar()

ROUTES = {
    "dashboard": render_dashboard,
    "lessons": render_lessons,
    "quiz": render_quiz,
    "quick_review": render_quick_review,
    "flashcards": render_flashcards,
    "study_plan": render_study_plan,
    "friends": render_friends,
    "leaderboard": render_leaderboard,
    "weekly_report": render_weekly_report,
    "notifications": render_notifications,
    "my_stats": render_my_stats,
    "favorites": render_favorites,
    "dev_panel": render_developer_panel,
}

ROUTES.get(st.session_state.page, render_dashboard)()
