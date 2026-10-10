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

SUBJECTS = {
    "maths": {"name": "الرياضيات", "icon": "📐", "color": "#4A90E2"},
    "french": {"name": "اللغة الفرنسية", "icon": "🇫🇷", "color": "#E74C3C"},
    "english": {"name": "اللغة الإنجليزية", "icon": "🇬🇧", "color": "#3498DB"},
    "history": {"name": "الاجتماعيات", "icon": "🌍", "color": "#F39C12"},
    "islamic": {"name": "التربية الإسلامية", "icon": "🕌", "color": "#27AE60"},
    "pc": {"name": "الفيزياء والكيمياء", "icon": "⚗️", "color": "#9B59B6"},
    "svt": {"name": "علوم الحياة والأرض", "icon": "🧬", "color": "#16A085"},
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
    "speed_demon": "⚡ البرق",
    "night_owl": "🦉 بومة الليل",
    "early_bird": "🐦 طائر الصباح",
    "perfectionist": "✨ المثالي",
    "social_butterfly": "🦋 اجتماعي",
    "note_master": "📝 سيد الملاحظات",
    "flashcard_king": "🃏 ملك البطاقات",
    "comeback": "🔄 العودة القوية",
    "marathon": "🏃 ماراثوني",
    "weekend_warrior": "⚔️ محارب الأسبوع",
}

RANKS = [
    (50, "🌟 أسطورة حية"),
    (35, "🏆 أسطورة"),
    (20, "👑 خبير"),
    (12, "🏅 متفوق"),
    (8, "⭐ متميز"),
    (5, "🎯 مجتهد"),
    (3, "📖 متعلّم"),
    (1, "🌱 مبتدئ"),
]

TRANSLATIONS = {
    "ar": {
        "home": "الرئيسية", "lessons": "الدروس", "quiz": "الاختبار", "quick_review": "مراجعة سريعة",
        "flashcards": "بطاقات تعليمية", "study_plan": "خطة الدراسة", "friends": "الأصدقاء",
        "leaderboard": "المتصدرون", "weekly_report": "التقرير الأسبوعي", "notifications": "الإشعارات",
        "my_stats": "إحصائياتي", "favorites": "المفضلة", "developer": "لوحة المطور",
        "logout": "تسجيل الخروج", "theme": "الثيم", "language": "اللغة",
        "profile": "الملف الشخصي", "login": "دخول", "register": "تسجيل", "student": "تلميذ",
        "welcome": "مرحباً", "points": "النقاط", "level": "المستوى", "quizzes": "الاختبارات",
        "perfect_scores": "العلامات الكاملة", "badges": "الشارات", "rank": "اللقب",
        "start_quiz": "ابدأ الاختبار", "score": "النتيجة", "correct": "صحيح", "wrong": "خطأ",
        "submit": "إرسال", "next": "التالي", "previous": "السابق", "time_left": "الوقت المتبقي",
        "search": "بحث", "all": "الكل", "add": "إضافة", "delete": "حذف", "save": "حفظ",
        "cancel": "إلغاء", "comments": "تعليقات", "rating": "تقييم", "notes": "ملاحظات",
        "discussion": "مناقشة", "reviews": "تقييمات", "no_data": "لا توجد بيانات",
        "daily_bonus": "مكافأة يومية", "streak": "سلسلة", "leaderboard_all": "الكل",
        "leaderboard_week": "هذا الأسبوع", "leaderboard_month": "هذا الشهر",
        "weaknesses": "نقاط الضعف", "strong_points": "نقاط القوة",
        "subject_stats": "إحصائيات المواد", "weekly_progress": "التقدم الأسبوعي",
        "complete": "مكتمل", "pending": "قيد الانتظار", "priority": "الأولوية",
        "target_date": "التاريخ المستهدف", "auto_generate": "توليد تلقائي",
        "add_friend": "إضافة صديق", "friend_username": "اسم المستخدم",
        "remove": "إزالة", "accept": "قبول", "reject": "رفض", "known": "معروف",
        "unknown": "غير معروف", "front": "الوجه", "back": "الظهر",
        "add_flashcard": "إضافة بطاقة", "subject": "المادة", "title": "العنوان",
        "content": "المحتوى", "image_url": "رابط الصورة", "pdf_url": "رابط PDF",
        "question": "السؤال", "option_a": "الخيار أ", "option_b": "الخيار ب",
        "option_c": "الخيار ج", "option_d": "الخيار د", "correct_answer": "الإجابة الصحيحة",
        "explanation": "الشرح", "add_lesson": "إضافة درس", "add_question": "إضافة سؤال",
        "lesson": "الدرس", "questions": "الأسئلة", "no_questions": "لا توجد أسئلة",
        "login_student": "دخول التلميذ", "login_developer": "دخول المطور",
        "register_new": "تسجيل جديد", "username": "اسم المستخدم",
        "password": "كلمة المرور", "full_name": "الاسم الكامل",
        "already_have": "لديك حساب؟", "no_account": "ليس لديك حساب؟",
        "error_login": "خطأ في تسجيل الدخول", "success_register": "تم التسجيل بنجاح",
        "error_register": "خطأ في التسجيل", "welcome_back": "مرحباً بعودتك",
        "files": "الملفات", "models": "نماذج الفروض", "download": "تحميل",
        "upload": "رفع", "file_name": "اسم الملف", "file_size": "الحجم",
        "uploaded_at": "تاريخ الرفع", "uploaded_by": "رفع بواسطة",
        "no_files": "لا توجد ملفات", "file_uploaded": "تم رفع الملف بنجاح",
        "confirm_delete": "هل أنت متأكد من الحذف؟", "yes": "نعم", "no": "لا",
        "download_all": "تحميل الكل", "file_type": "النوع", "actions": "إجراءات",
    },
    "fr": {
        "home": "Accueil", "lessons": "Leçons", "quiz": "Quiz", "quick_review": "Révision rapide",
        "flashcards": "Cartes", "study_plan": "Plan d'étude", "friends": "Amis",
        "leaderboard": "Classement", "weekly_report": "Rapport hebdo", "notifications": "Notifications",
        "my_stats": "Mes stats", "favorites": "Favoris", "developer": "Panneau dev",
        "logout": "Déconnexion", "theme": "Thème", "language": "Langue",
        "profile": "Profil", "login": "Connexion", "register": "Inscription", "student": "Élève",
        "welcome": "Bienvenue", "points": "Points", "level": "Niveau", "quizzes": "Quiz",
        "perfect_scores": "Scores parfaits", "badges": "Badges", "rank": "Rang",
        "start_quiz": "Commencer", "score": "Score", "correct": "Correct", "wrong": "Faux",
        "submit": "Envoyer", "next": "Suivant", "previous": "Précédent", "time_left": "Temps restant",
        "search": "Recherche", "all": "Tout", "add": "Ajouter", "delete": "Supprimer", "save": "Sauver",
        "cancel": "Annuler", "comments": "Commentaires", "rating": "Note", "notes": "Notes",
        "discussion": "Discussion", "reviews": "Avis", "no_data": "Aucune donnée",
        "daily_bonus": "Bonus quotidien", "streak": "Série", "leaderboard_all": "Tout",
        "leaderboard_week": "Cette semaine", "leaderboard_month": "Ce mois",
        "weaknesses": "Points faibles", "strong_points": "Points forts",
        "subject_stats": "Stats par matière", "weekly_progress": "Progrès hebdo",
        "complete": "Terminé", "pending": "En attente", "priority": "Priorité",
        "target_date": "Date cible", "auto_generate": "Générer auto",
        "add_friend": "Ajouter ami", "friend_username": "Nom d'utilisateur",
        "remove": "Retirer", "accept": "Accepter", "reject": "Refuser", "known": "Connu",
        "unknown": "Inconnu", "front": "Recto", "back": "Verso",
        "add_flashcard": "Ajouter carte", "subject": "Matière", "title": "Titre",
        "content": "Contenu", "image_url": "URL image", "pdf_url": "URL PDF",
        "question": "Question", "option_a": "Option A", "option_b": "Option B",
        "option_c": "Option C", "option_d": "Option D", "correct_answer": "Réponse correcte",
        "explanation": "Explication", "add_lesson": "Ajouter leçon", "add_question": "Ajouter question",
        "lesson": "Leçon", "questions": "Questions", "no_questions": "Aucune question",
        "login_student": "Connexion élève", "login_developer": "Connexion dev",
        "register_new": "Inscription", "username": "Nom d'utilisateur",
        "password": "Mot de passe", "full_name": "Nom complet",
        "already_have": "Déjà un compte?", "no_account": "Pas de compte?",
        "error_login": "Erreur de connexion", "success_register": "Inscription réussie",
        "error_register": "Erreur d'inscription", "welcome_back": "Bon retour",
        "files": "Fichiers", "models": "Modèles d'examens", "download": "Télécharger",
        "upload": "Téléverser", "file_name": "Nom du fichier", "file_size": "Taille",
        "uploaded_at": "Date", "uploaded_by": "Par",
        "no_files": "Aucun fichier", "file_uploaded": "Fichier téléversé",
        "confirm_delete": "Confirmer la suppression?", "yes": "Oui", "no": "Non",
        "download_all": "Tout télécharger", "file_type": "Type", "actions": "Actions",
    },
    "en": {
        "home": "Home", "lessons": "Lessons", "quiz": "Quiz", "quick_review": "Quick Review",
        "flashcards": "Flashcards", "study_plan": "Study Plan", "friends": "Friends",
        "leaderboard": "Leaderboard", "weekly_report": "Weekly Report", "notifications": "Notifications",
        "my_stats": "My Stats", "favorites": "Favorites", "developer": "Developer Panel",
        "logout": "Logout", "theme": "Theme", "language": "Language",
        "profile": "Profile", "login": "Login", "register": "Register", "student": "Student",
        "welcome": "Welcome", "points": "Points", "level": "Level", "quizzes": "Quizzes",
        "perfect_scores": "Perfect Scores", "badges": "Badges", "rank": "Rank",
        "start_quiz": "Start Quiz", "score": "Score", "correct": "Correct", "wrong": "Wrong",
        "submit": "Submit", "next": "Next", "previous": "Previous", "time_left": "Time Left",
        "search": "Search", "all": "All", "add": "Add", "delete": "Delete", "save": "Save",
        "cancel": "Cancel", "comments": "Comments", "rating": "Rating", "notes": "Notes",
        "discussion": "Discussion", "reviews": "Reviews", "no_data": "No data",
        "daily_bonus": "Daily Bonus", "streak": "Streak", "leaderboard_all": "All",
        "leaderboard_week": "This Week", "leaderboard_month": "This Month",
        "weaknesses": "Weaknesses", "strong_points": "Strong Points",
        "subject_stats": "Subject Stats", "weekly_progress": "Weekly Progress",
        "complete": "Complete", "pending": "Pending", "priority": "Priority",
        "target_date": "Target Date", "auto_generate": "Auto Generate",
        "add_friend": "Add Friend", "friend_username": "Username",
        "remove": "Remove", "accept": "Accept", "reject": "Reject", "known": "Known",
        "unknown": "Unknown", "front": "Front", "back": "Back",
        "add_flashcard": "Add Flashcard", "subject": "Subject", "title": "Title",
        "content": "Content", "image_url": "Image URL", "pdf_url": "PDF URL",
        "question": "Question", "option_a": "Option A", "option_b": "Option B",
        "option_c": "Option C", "option_d": "Option D", "correct_answer": "Correct Answer",
        "explanation": "Explanation", "add_lesson": "Add Lesson", "add_question": "Add Question",
        "lesson": "Lesson", "questions": "Questions", "no_questions": "No questions",
        "login_student": "Student Login", "login_developer": "Developer Login",
        "register_new": "Register", "username": "Username",
        "password": "Password", "full_name": "Full Name",
        "already_have": "Already have an account?", "no_account": "No account?",
        "error_login": "Login error", "success_register": "Registration successful",
        "error_register": "Registration error", "welcome_back": "Welcome back",
        "files": "Files", "models": "Exam Models", "download": "Download",
        "upload": "Upload", "file_name": "File name", "file_size": "Size",
        "uploaded_at": "Date", "uploaded_by": "By",
        "no_files": "No files", "file_uploaded": "File uploaded successfully",
        "confirm_delete": "Confirm delete?", "yes": "Yes", "no": "No",
        "download_all": "Download all", "file_type": "Type", "actions": "Actions",
    },
}

# ============================================================
# DATABASE FUNCTIONS
# ============================================================

def get_db():
    conn = sqlite3.connect(DB_NAME, check_same_thread=False)
    conn.row_factory = sqlite3.Row
    return conn

def init_db():
    conn = get_db()
    c = conn.cursor()
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
        created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
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
        explanation TEXT,
        FOREIGN KEY (lesson_id) REFERENCES lessons(id)
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
        streak INTEGER DEFAULT 0
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
    # NEW TABLES
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
        owner TEXT,
        downloads INTEGER DEFAULT 0,
        created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
    )""")
    c.execute("""CREATE TABLE IF NOT EXISTS exam_models (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        subject TEXT NOT NULL,
        title TEXT NOT NULL,
        year TEXT,
        semester TEXT,
        description TEXT,
        file_path TEXT NOT NULL,
        file_name TEXT NOT NULL,
        file_size INTEGER DEFAULT 0,
        owner TEXT,
        downloads INTEGER DEFAULT 0,
        created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
    )""")
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

def update_user_stats(u, points=0, quiz=False, perfect=False, subject=None):
    conn = get_db()
    c = conn.cursor()
    c.execute("SELECT * FROM user_stats WHERE username = ?", (u,))
    row = c.fetchone()
    if not row:
        c.execute("INSERT INTO user_stats (username) VALUES (?)", (u,))
        conn.commit()
        c.execute("SELECT * FROM user_stats WHERE username = ?", (u,))
        row = c.fetchone()
    total_points = row["total_points"] + points
    level = total_points // 100 + 1
    quizzes_taken = row["quizzes_taken"] + (1 if quiz else 0)
    perfect_scores = row["perfect_scores"] + (1 if perfect else 0)
    subjects = set()
    c.execute("SELECT DISTINCT subject FROM quiz_history WHERE username = ?", (u,))
    for r in c.fetchall():
        if r["subject"]:
            subjects.add(r["subject"])
    if subject:
        subjects.add(subject)
    unique_subjects = len(subjects)
    c.execute("""UPDATE user_stats SET total_points=?, level=?, quizzes_taken=?,
                 perfect_scores=?, unique_subjects=? WHERE username=?""",
              (total_points, level, quizzes_taken, perfect_scores, unique_subjects, u))
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
    if stats["quizzes_taken"] >= 1:
        earned.add("first_quiz")
    if stats["perfect_scores"] >= 1:
        earned.add("perfect")
    if stats["quizzes_taken"] >= 5:
        earned.add("5_quizzes")
    if stats["quizzes_taken"] >= 10:
        earned.add("10_quizzes")
    if stats["quizzes_taken"] >= 25:
        earned.add("25_quizzes")
    if stats["quizzes_taken"] >= 50:
        earned.add("50_quizzes")
    if stats["quizzes_taken"] >= 100:
        earned.add("100_quizzes")
    if stats["level"] >= 5:
        earned.add("level_5")
    if stats["level"] >= 10:
        earned.add("level_10")
    if stats["level"] >= 20:
        earned.add("level_20")
    if stats["level"] >= 50:
        earned.add("level_50")
    if stats["unique_subjects"] >= 7:
        earned.add("all_subjects")
    if stats["streak"] >= 7:
        earned.add("streak_7")
    if stats["streak"] >= 30:
        earned.add("streak_30")
    hour = datetime.now().hour
    if hour >= 0 and hour < 5:
        earned.add("night_owl")
    if hour >= 5 and hour < 7:
        earned.add("early_bird")
    conn2 = get_db()
    c2 = conn2.cursor()
    c2.execute("SELECT COUNT(*) as cnt FROM notes WHERE username = ?", (u,))
    if c2.fetchone()["cnt"] >= 10:
        earned.add("note_master")
    c2.execute("SELECT COUNT(*) as cnt FROM flashcards WHERE username = ?", (u,))
    if c2.fetchone()["cnt"] >= 20:
        earned.add("flashcard_king")
    c2.execute("SELECT COUNT(*) as cnt FROM friends WHERE username = ? AND status = 'accepted'", (u,))
    if c2.fetchone()["cnt"] >= 5:
        earned.add("social_butterfly")
    c2.execute("SELECT COUNT(*) as cnt FROM quiz_history WHERE username = ? AND percent = 100", (u,))
    if c2.fetchone()["cnt"] >= 10:
        earned.add("perfectionist")
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
    if last == yesterday:
        streak += 1
    else:
        streak = 1
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

def load_lessons(subject=None, language=None, owner=None, search=None):
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
    if owner:
        q += " AND owner = ?"
        params.append(owner)
    if search:
        q += " AND (title LIKE ? OR content LIKE ?)"
        params.extend([f"%{search}%", f"%{search}%"])
    q += " ORDER BY created_at DESC"
    c.execute(q, params)
    rows = c.fetchall()
    conn.close()
    return rows

def add_lesson(subject, language, title, content, image_url, pdf_url, owner):
    conn = get_db()
    c = conn.cursor()
    c.execute("""INSERT INTO lessons (subject, language, title, content, image_url, pdf_url, owner)
                 VALUES (?, ?, ?, ?, ?, ?, ?)""",
              (subject, language, title, content, image_url, pdf_url, owner))
    conn.commit()
    lid = c.lastrowid
    conn.close()
    return lid

def delete_lesson(lid):
    conn = get_db()
    c = conn.cursor()
    c.execute("DELETE FROM questions WHERE lesson_id = ?", (lid,))
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
        return
    with open(path, "rb") as f:
        b64 = base64.b64encode(f.read()).decode()
    st.markdown(f'<iframe src="data:application/pdf;base64,{b64}" width="100%" height="600" style="border-radius:12px;"></iframe>', unsafe_allow_html=True)

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
# FILES DATABASE FUNCTIONS (NEW)
# ============================================================

def add_file_record(subject, category, title, description, file_path, file_name, file_size, file_type, owner):
    conn = get_db()
    c = conn.cursor()
    c.execute("""INSERT INTO files (subject, category, title, description, file_path, file_name, file_size, file_type, owner)
                 VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)""",
              (subject, category, title, description, file_path, file_name, file_size, file_type, owner))
    conn.commit()
    fid = c.lastrowid
    conn.close()
    return fid

def get_files(subject=None, category=None, search=None, owner=None):
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
    if owner:
        q += " AND owner = ?"
        params.append(owner)
    if search:
        q += " AND (title LIKE ? OR description LIKE ? OR file_name LIKE ?)"
        params.extend([f"%{search}%", f"%{search}%", f"%{search}%"])
    q += " ORDER BY created_at DESC"
    c.execute(q, params)
    rows = c.fetchall()
    conn.close()
    return rows

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
    c.execute("DELETE FROM files WHERE id = ?", (fid,))
    conn.commit()
    conn.close()

def increment_file_download(fid):
    conn = get_db()
    c = conn.cursor()
    c.execute("UPDATE files SET downloads = downloads + 1 WHERE id = ?", (fid,))
    conn.commit()
    conn.close()

def format_size(size):
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
    if "pdf" in ft or name.endswith(".pdf"):
        return "📕"
    elif name.endswith(".doc") or name.endswith(".docx") or "word" in ft:
        return "📘"
    elif name.endswith(".xls") or name.endswith(".xlsx") or "excel" in ft:
        return "📗"
    elif name.endswith(".ppt") or name.endswith(".pptx") or "powerpoint" in ft:
        return "📙"
    elif name.endswith((".png", ".jpg", ".jpeg", ".gif", ".bmp", ".webp")) or "image" in ft:
        return "🖼️"
    elif name.endswith((".mp4", ".avi", ".mov", ".mkv", ".webm")) or "video" in ft:
        return "🎬"
    elif name.endswith((".mp3", ".wav", ".ogg", ".m4a")) or "audio" in ft:
        return "🎵"
    elif name.endswith((".zip", ".rar", ".7z", ".tar", ".gz")):
        return "🗜️"
    elif name.endswith((".py", ".js", ".html", ".css", ".java", ".cpp")):
        return "💻"
    else:
        return "📄"

# ============================================================
# EXAM MODELS DATABASE FUNCTIONS (NEW)
# ============================================================

def add_exam_model(subject, title, year, semester, description, file_path, file_name, file_size, owner):
    conn = get_db()
    c = conn.cursor()
    c.execute("""INSERT INTO exam_models (subject, title, year, semester, description, file_path, file_name, file_size, owner)
                 VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)""",
              (subject, title, year, semester, description, file_path, file_name, file_size, owner))
    conn.commit()
    mid = c.lastrowid
    conn.close()
    return mid

def get_exam_models(subject=None, year=None, semester=None, search=None, owner=None):
    conn = get_db()
    c = conn.cursor()
    q = "SELECT * FROM exam_models WHERE 1=1"
    params = []
    if subject and subject != "all":
        q += " AND subject = ?"
        params.append(subject)
    if year and year != "all":
        q += " AND year = ?"
        params.append(year)
    if semester and semester != "all":
        q += " AND semester = ?"
        params.append(semester)
    if owner:
        q += " AND owner = ?"
        params.append(owner)
    if search:
        q += " AND (title LIKE ? OR description LIKE ? OR file_name LIKE ?)"
        params.extend([f"%{search}%", f"%{search}%", f"%{search}%"])
    q += " ORDER BY created_at DESC"
    c.execute(q, params)
    rows = c.fetchall()
    conn.close()
    return rows

def delete_exam_model(mid):
    conn = get_db()
    c = conn.cursor()
    c.execute("SELECT file_path FROM exam_models WHERE id = ?", (mid,))
    row = c.fetchone()
    if row and row["file_path"]:
        try:
            if os.path.exists(row["file_path"]):
                os.remove(row["file_path"])
        except Exception:
            pass
    c.execute("DELETE FROM exam_models WHERE id = ?", (mid,))
    conn.commit()
    conn.close()

def increment_exam_download(mid):
    conn = get_db()
    c = conn.cursor()
    c.execute("UPDATE exam_models SET downloads = downloads + 1 WHERE id = ?", (mid,))
    conn.commit()
    conn.close()

def get_exam_years():
    conn = get_db()
    c = conn.cursor()
    c.execute("SELECT DISTINCT year FROM exam_models WHERE year IS NOT NULL AND year != '' ORDER BY year DESC")
    rows = c.fetchall()
    conn.close()
    return [r["year"] for r in rows]

# ============================================================
# DOWNLOAD HELPER
# ============================================================

def make_download_button(file_path, file_name, key, label="⬇️ تحميل"):
    if not file_path or not os.path.exists(file_path):
        st.warning("الملف غير موجود")
        return
    try:
        with open(file_path, "rb") as f:
            data = f.read()
        st.download_button(
            label=label,
            data=data,
            file_name=file_name,
            mime="application/octet-stream",
            key=key,
            use_container_width=True
        )
    except Exception as e:
        st.error(f"خطأ في التحميل: {e}")

# ============================================================
# THEME & TRANSLATION
# ============================================================

def apply_theme():
    theme_key = st.session_state.get("theme", "fcb")
    t = THEMES[theme_key]
    css = f"""
    <style>
    @import url('https://fonts.googleapis.com/css2?family=Cairo:wght@400;600;700;900&display=swap');
    * {{ font-family: 'Cairo', sans-serif; direction: rtl; }}
    .stApp {{ background-color: {t['bg']}; color: {t['text']}; }}
    .main .block-container {{ padding: 1rem 2rem; max-width: 1200px; }}
    h1, h2, h3, h4, h5, h6 {{ color: {t['text']}; }}
    p, span, div, label {{ color: {t['text']}; }}
    .stButton > button {{
        background: linear-gradient(135deg, {t['accent']}, {t['border']});
        color: {t['text']};
        border: 1px solid {t['border']};
        border-radius: 12px;
        padding: 0.5rem 1.2rem;
        font-weight: 700;
        transition: all 0.3s;
    }}
    .stButton > button:hover {{
        transform: translateY(-2px);
        box-shadow: 0 8px 20px {t['accent']}66;
    }}
    .stDownloadButton > button {{
        background: linear-gradient(135deg, {t['highlight']}, {t['accent']});
        color: #000;
        border: none;
        border-radius: 12px;
        font-weight: 700;
        width: 100%;
    }}
    .stDownloadButton > button:hover {{
        transform: translateY(-2px);
        box-shadow: 0 8px 20px {t['highlight']}66;
    }}
    .stTextInput > div > div > input, .stTextArea > div > div > textarea, .stSelectbox > div > div {{
        background-color: {t['card']} !important;
        color: {t['text']} !important;
        border: 1px solid {t['border']} !important;
        border-radius: 10px !important;
    }}
    .stTabs [data-baseweb="tab"] {{
        background-color: {t['card']};
        color: {t['text']};
        border-radius: 10px 10px 0 0;
        padding: 0.5rem 1rem;
    }}
    .stTabs [aria-selected="true"] {{
        background-color: {t['accent']} !important;
        color: #fff !important;
    }}
    .card {{
        background-color: {t['card']};
        border: 1px solid {t['border']};
        border-radius: 16px;
        padding: 1.2rem;
        margin: 0.8rem 0;
        box-shadow: 0 4px 15px rgba(0,0,0,0.3);
        transition: all 0.3s;
    }}
    .card:hover {{
        transform: translateY(-3px);
        box-shadow: 0 8px 25px {t['accent']}44;
    }}
    .file-card {{
        background-color: {t['card']};
        border: 1px solid {t['border']};
        border-radius: 14px;
        padding: 1rem;
        margin: 0.6rem 0;
        display: flex;
        align-items: center;
        gap: 1rem;
        transition: all 0.3s;
    }}
    .file-card:hover {{
        border-color: {t['accent']};
        box-shadow: 0 6px 20px {t['accent']}33;
    }}
    .file-icon {{ font-size: 2.5rem; }}
    .file-info {{ flex: 1; }}
    .file-title {{ font-weight: 700; font-size: 1.1rem; color: {t['text']}; }}
    .file-meta {{ font-size: 0.85rem; opacity: 0.75; color: {t['text']}; }}
    .stat-box {{
        background: linear-gradient(135deg, {t['card']}, {t['secondary']});
        border: 1px solid {t['border']};
        border-radius: 14px;
        padding: 1rem;
        text-align: center;
        margin: 0.3rem;
    }}
    .stat-number {{ font-size: 2rem; font-weight: 900; color: {t['accent']}; }}
    .badge {{
        display: inline-block;
        background: {t['secondary']};
        border: 1px solid {t['border']};
        border-radius: 20px;
        padding: 0.3rem 0.8rem;
        margin: 0.2rem;
        font-size: 0.9rem;
    }}
    .badge-earned {{
        background: linear-gradient(135deg, {t['accent']}, {t['highlight']});
        color: #000;
        font-weight: 700;
    }}
    .footer {{
        text-align: center;
        padding: 1.5rem;
        color: {t['text']};
        opacity: 0.6;
        font-size: 0.85rem;
        border-top: 1px solid {t['border']};
        margin-top: 2rem;
    }}
    .header-banner {{
        background: linear-gradient(135deg, {t['accent']}, {t['border']});
        border-radius: 16px;
        padding: 1.5rem;
        text-align: center;
        margin-bottom: 1.5rem;
    }}
    .header-banner h1 {{ color: #fff; margin: 0; }}
    .header-banner p {{ color: #fff; opacity: 0.9; margin: 0.3rem 0 0 0; }}
    .sidebar .sidebar-content {{ background-color: {t['secondary']}; }}
    section[data-testid="stSidebar"] {{
        background-color: {t['secondary']} !important;
        border-left: 1px solid {t['border']};
    }}
    .stProgress > div > div > div > div {{
        background: linear-gradient(90deg, {t['accent']}, {t['highlight']});
    }}
    .stRadio > div {{ gap: 0.5rem; }}
    .stRadio label {{ color: {t['text']} !important; }}
    .stCheckbox label {{ color: {t['text']} !important; }}
    .stMetric label {{ color: {t['text']} !important; }}
    .stMetric value {{ color: {t['accent']} !important; }}
    div[data-testid="stExpander"] {{
        background-color: {t['card']};
        border: 1px solid {t['border']};
        border-radius: 12px;
    }}
    .stAlert {{ border-radius: 12px; }}
    .rec-card {{
        background: {t['card']};
        border-right: 4px solid {t['accent']};
        border-radius: 12px;
        padding: 1rem;
        margin: 0.5rem 0;
    }}
    .category-chip {{
        display: inline-block;
        background: {t['accent']};
        color: #fff;
        border-radius: 12px;
        padding: 0.2rem 0.7rem;
        font-size: 0.8rem;
        margin: 0.1rem;
    }}
    </style>
    """
    st.markdown(css, unsafe_allow_html=True)

def T(key):
    lang = st.session_state.get("language", "ar")
    return TRANSLATIONS.get(lang, TRANSLATIONS["ar"]).get(key, key)

def footer():
    st.markdown('<div class="footer">© 2026 Soufiane Ouhazza — 3AC RevisioMaroc</div>', unsafe_allow_html=True)

# ============================================================
# AUTH PAGES
# ============================================================

def render_auth_home():
    st.markdown("""
    <div class="header-banner">
        <h1>📚 3AC RevisioMaroc</h1>
        <p>منصة المراجعة للتلاميذ — السنة الثالثة إعدادي</p>
    </div>
    """, unsafe_allow_html=True)
    col1, col2, col3 = st.columns(3)
    with col1:
        if st.button("🎓 تلميذ", use_container_width=True):
            st.session_state.auth_page = "student_login"
            st.rerun()
    with col2:
        if st.button("🛠️ مطور", use_container_width=True):
            st.session_state.auth_page = "developer_login"
            st.rerun()
    with col3:
        if st.button("📝 تسجيل جديد", use_container_width=True):
            st.session_state.auth_page = "register"
            st.rerun()
    st.markdown("### ✨ مميزات المنصة")
    c1, c2, c3, c4 = st.columns(4)
    with c1:
        st.markdown('<div class="card" style="text-align:center;"><div style="font-size:2rem;">📝</div><b>اختبارات تفاعلية</b></div>', unsafe_allow_html=True)
    with c2:
        st.markdown('<div class="card" style="text-align:center;"><div style="font-size:2rem;">📂</div><b>ملفات الدروس</b></div>', unsafe_allow_html=True)
    with c3:
        st.markdown('<div class="card" style="text-align:center;"><div style="font-size:2rem;">📄</div><b>نماذج الفروض</b></div>', unsafe_allow_html=True)
    with c4:
        st.markdown('<div class="card" style="text-align:center;"><div style="font-size:2rem;">🏆</div><b>نظام النقاط</b></div>', unsafe_allow_html=True)
    footer()

def render_student_login():
    st.markdown('<div class="header-banner"><h1>🎓 دخول التلميذ</h1></div>', unsafe_allow_html=True)
    with st.form("student_login"):
        u = st.text_input(T("username"))
        p = st.text_input(T("password"), type="password")
        if st.form_submit_button(T("login"), use_container_width=True):
            user = authenticate(u, p)
            if user and user["role"] in ("student", "developer"):
                st.session_state.authenticated = True
                st.session_state.username = u
                st.session_state.role = user["role"]
                st.session_state.full_name = user["full_name"]
                st.session_state.page = "dashboard"
                bonus, streak = check_daily_bonus(u)
                if bonus > 0:
                    st.success(f"🎁 مكافأة يومية: +{bonus} نقطة! (سلسلة: {streak} أيام)")
                st.rerun()
            else:
                st.error(T("error_login"))
    if st.button("← رجوع"):
        st.session_state.auth_page = "home"
        st.rerun()
    footer()

def render_developer_login():
    st.markdown('<div class="header-banner"><h1>🛠️ دخول المطور</h1></div>', unsafe_allow_html=True)
    with st.form("dev_login"):
        u = st.text_input(T("username"))
        p = st.text_input(T("password"), type="password")
        if st.form_submit_button(T("login"), use_container_width=True):
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
        st.session_state.auth_page = "home"
        st.rerun()
    footer()

def render_register():
    st.markdown('<div class="header-banner"><h1>📝 تسجيل جديد</h1></div>', unsafe_allow_html=True)
    with st.form("register"):
        n = st.text_input(T("full_name"))
        u = st.text_input(T("username"))
        p = st.text_input(T("password"), type="password")
        p2 = st.text_input("تأكيد كلمة المرور", type="password")
        if st.form_submit_button(T("register"), use_container_width=True):
            if not u or not p or not n:
                st.error("املأ جميع الحقول")
            elif len(p) < 4:
                st.error("كلمة المرور قصيرة جداً")
            elif p != p2:
                st.error("كلمتا المرور غير متطابقتين")
            elif register_user(u, p, n):
                st.success(T("success_register") + " ✅")
                st.session_state.auth_page = "student_login"
                st.rerun()
            else:
                st.error(T("error_register") + " — اسم المستخدم مستعمل")
    if st.button("← رجوع"):
        st.session_state.auth_page = "home"
        st.rerun()
    footer()

def render_auth_page():
    if "auth_page" not in st.session_state:
        st.session_state.auth_page = "home"
    page = st.session_state.auth_page
    if page == "home":
        render_auth_home()
    elif page == "student_login":
        render_student_login()
    elif page == "developer_login":
        render_developer_login()
    elif page == "register":
        render_register()
    else:
        render_auth_home()

# ============================================================
# DASHBOARD
# ============================================================

def render_dashboard():
    u = st.session_state.username
    stats = get_user_stats(u)
    st.markdown(f'<div class="header-banner"><h1>مرحباً {st.session_state.full_name or u} 👋</h1><p>لنواصل المراجعة!</p></div>', unsafe_allow_html=True)
    level = stats["level"] if stats else 1
    points = stats["total_points"] if stats else 0
    rank = get_rank(level)
    c1, c2, c3, c4 = st.columns(4)
    with c1:
        st.markdown(f'<div class="stat-box"><div class="stat-number">{points}</div><div>النقاط</div></div>', unsafe_allow_html=True)
    with c2:
        st.markdown(f'<div class="stat-box"><div class="stat-number">{level}</div><div>المستوى</div></div>', unsafe_allow_html=True)
    with c3:
        st.markdown(f'<div class="stat-box"><div class="stat-number">{stats["quizzes_taken"] if stats else 0}</div><div>الاختبارات</div></div>', unsafe_allow_html=True)
    with c4:
        st.markdown(f'<div class="stat-box"><div class="stat-number">{rank.split()[0]}</div><div>{rank}</div></div>', unsafe_allow_html=True)
    progress = (points % 100) / 100
    st.progress(progress, text=f"التقدم نحو المستوى {level + 1}: {points % 100}/100")
    recs = get_recommendations(u)
    if recs:
        st.markdown("### 💡 توصيات ذكية")
        for r in recs:
            st.markdown(f'<div class="rec-card"><b>{r["icon"]} {r["title"]}</b><br><small>{r["desc"]}</small></div>', unsafe_allow_html=True)
    st.markdown("### 📚 المواد الدراسية")
    cols = st.columns(4)
    for i, (key, subj) in enumerate(SUBJECTS.items()):
        with cols[i % 4]:
            st.markdown(f"""
            <div class="card" style="border-color:{subj['color']};text-align:center;">
                <div style="font-size:2.5rem;">{subj['icon']}</div>
                <div style="font-weight:700;font-size:1.1rem;">{subj['name']}</div>
            </div>
            """, unsafe_allow_html=True)
            if st.button(f"تصفح", key=f"subj_{key}", use_container_width=True):
                st.session_state.filter_subject = key
                st.session_state.page = "lessons"
                st.rerun()
    st.markdown("### ⚡ إجراءات سريعة")
    c1, c2, c3, c4 = st.columns(4)
    with c1:
        if st.button("🎯 التحدي اليومي", use_container_width=True):
            st.session_state.page = "daily_challenge"
            st.rerun()
    with c2:
        if st.button("⏱️ مؤقت المراجعة", use_container_width=True):
            st.session_state.page = "pomodoro"
            st.rerun()
    with c3:
        if st.button("📂 الملفات", use_container_width=True):
            st.session_state.page = "files"
            st.rerun()
    with c4:
        if st.button("📄 نماذج الفروض", use_container_width=True):
            st.session_state.page = "exam_models"
            st.rerun()
    # Recent files
    st.markdown("### 📂 أحدث الملفات المرفوعة")
    recent_files = get_files()[:5]
    if recent_files:
        for f in recent_files:
            subj = SUBJECTS.get(f["subject"], {"name": f["subject"] or "عام", "icon": "📄"})
            icon = get_file_icon(f["file_type"], f["file_name"])
            st.markdown(f"""
            <div class="file-card">
                <div class="file-icon">{icon}</div>
                <div class="file-info">
                    <div class="file-title">{f['title']}</div>
                    <div class="file-meta">{subj['icon']} {subj['name']} • {format_size(f['file_size'])} • ⬇️ {f['downloads']}</div>
                </div>
            </div>
            """, unsafe_allow_html=True)
    else:
        st.info("لا توجد ملفات بعد")
    st.markdown("### 📄 أحدث نماذج الفروض")
    recent_models = get_exam_models()[:5]
    if recent_models:
        for m in recent_models:
            subj = SUBJECTS.get(m["subject"], {"name": m["subject"], "icon": "📄"})
            icon = get_file_icon("", m["file_name"])
            st.markdown(f"""
            <div class="file-card">
                <div class="file-icon">{icon}</div>
                <div class="file-info">
                    <div class="file-title">{m['title']}</div>
                    <div class="file-meta">{subj['icon']} {subj['name']} • {m['year'] or ''} • {m['semester'] or ''} • ⬇️ {m['downloads']}</div>
                </div>
            </div>
            """, unsafe_allow_html=True)
    else:
        st.info("لا توجد نماذج بعد")
    footer()

# ============================================================
# LESSONS
# ============================================================

def _render_reviews(lid):
    st.markdown("#### ⭐ التقييمات")
    avg = get_avg_rating(lid)
    if avg:
        st.markdown(f"**المتوسط: {avg:.1f}/5** " + "⭐" * int(avg))
    reviews = get_reviews(lid)
    with st.form(f"review_form_{lid}"):
        rating = st.slider("تقييمك", 1, 5, 5)
        comment = st.text_area("تعليقك")
        if st.form_submit_button("إرسال التقييم"):
            add_review(lid, st.session_state.username, rating, comment)
            st.success("تم إضافة التقييم")
            st.rerun()
    for r in reviews:
        st.markdown(f"**{r['username']}** — {'⭐' * r['rating']}")
        if r["comment"]:
            st.write(r["comment"])
        st.divider()

def _render_discussion(lid):
    st.markdown("#### 💬 المناقشة")
    messages = get_messages(lid)
    for m in messages:
        st.markdown(f"**{m['username']}** _({m['created_at'][:16]})_")
        st.write(m["message"])
        st.divider()
    with st.form(f"msg_form_{lid}"):
        msg = st.text_area("رسالتك")
        if st.form_submit_button("إرسال"):
            if msg.strip():
                add_message(lid, st.session_state.username, msg.strip())
                st.rerun()

def _render_notes(lid):
    st.markdown("#### 📝 ملاحظاتي")
    notes = get_notes(st.session_state.username, lid)
    with st.form(f"note_form_{lid}"):
        note = st.text_area("ملاحظة جديدة")
        if st.form_submit_button("حفظ الملاحظة"):
            if note.strip():
                add_note(st.session_state.username, lid, note.strip())
                st.rerun()
    for n in notes:
        st.markdown(f"_{n['created_at'][:16]}_")
        st.write(n["note"])
        if st.button("🗑️", key=f"del_note_{n['id']}"):
            delete_note(n["id"])
            st.rerun()
        st.divider()

def _render_lesson_card(lesson):
    lid = lesson["id"]
    subj = SUBJECTS.get(lesson["subject"], {"name": lesson["subject"], "icon": "📖", "color": "#888"})
    fav = is_favorite(st.session_state.username, lid)
    col1, col2 = st.columns([5, 1])
    with col1:
        st.markdown(f"### {subj['icon']} {lesson['title']}")
        st.caption(f"{subj['name']} — {lesson['language']} — {lesson['created_at'][:10]}")
    with col2:
        if st.button("❤️" if fav else "🤍", key=f"fav_{lid}"):
            toggle_favorite(st.session_state.username, lid)
            st.rerun()
    tabs = st.tabs(["📖 المحتوى", "⭐ التقييمات", "💬 المناقشة", "📝 ملاحظاتي"])
    with tabs[0]:
        if lesson["image_url"]:
            st.image(lesson["image_url"], use_container_width=True)
        st.write(lesson["content"] or "")
        if lesson["pdf_url"]:
            render_pdf(lesson["pdf_url"])
        questions = load_questions(lid)
        if questions:
            if st.button(f"🚀 ابدأ الاختبار ({len(questions)} أسئلة)", key=f"start_quiz_{lid}"):
                st.session_state.quiz_lesson_id = lid
                st.session_state.quiz_lesson_title = lesson["title"]
                st.session_state.quiz_subject = lesson["subject"]
                st.session_state.quiz_questions = [dict(q) for q in questions]
                st.session_state.quiz_answers = {}
                st.session_state.quiz_start_time = time.time()
                st.session_state.page = "quiz"
                st.rerun()
    with tabs[1]:
        _render_reviews(lid)
    with tabs[2]:
        _render_discussion(lid)
    with tabs[3]:
        _render_notes(lid)

def render_lessons():
    st.markdown('<div class="header-banner"><h1>📖 الدروس</h1></div>', unsafe_allow_html=True)
    c1, c2, c3 = st.columns(3)
    with c1:
        subject = st.selectbox("المادة", ["all"] + list(SUBJECTS.keys()),
                               format_func=lambda x: "الكل" if x == "all" else f"{SUBJECTS[x]['icon']} {SUBJECTS[x]['name']}",
                               key="filter_subject_select")
    with c2:
        language = st.selectbox("اللغة", ["all", "ar", "fr", "en"],
                                format_func=lambda x: {"all": "الكل", "ar": "العربية", "fr": "الفرنسية", "en": "الإنجليزية"}.get(x, x))
    with c3:
        search = st.text_input("🔍 بحث")
    if "filter_subject" in st.session_state and st.session_state.filter_subject != "all":
        subject = st.session_state.filter_subject
        st.session_state.filter_subject = "all"
    lessons = load_lessons(subject=subject, language=language, search=search)
    if not lessons:
        st.info("لا توجد دروس")
    for lesson in lessons:
        with st.container():
            _render_lesson_card(lesson)
            st.divider()
    footer()

# ============================================================
# FILES PAGE (NEW)
# ============================================================

def render_files():
    st.markdown('<div class="header-banner"><h1>📂 ملفات الدروس والملازم</h1><p>حمّل الملفات التي رفعها الأساتذة والمطورون</p></div>', unsafe_allow_html=True)
    tab1, tab2 = st.tabs(["📥 تصفح الملفات", "⬆️ رفع ملف"])
    with tab1:
        c1, c2, c3 = st.columns(3)
        with c1:
            subject_filter = st.selectbox("المادة", ["all"] + list(SUBJECTS.keys()),
                                          format_func=lambda x: "الكل" if x == "all" else f"{SUBJECTS[x]['icon']} {SUBJECTS[x]['name']}",
                                          key="files_subject")
        with c2:
            category_filter = st.selectbox("النوع", ["all", "files", "lessons", "exercises", "summaries", "books"],
                                           format_func=lambda x: {
                                               "all": "الكل", "files": "ملفات عامة", "lessons": "دروس",
                                               "exercises": "تمارين", "summaries": "ملخصات", "books": "كتب"
                                           }.get(x, x), key="files_category")
        with c3:
            search_files = st.text_input("🔍 بحث", key="files_search")
        files_list = get_files(subject=subject_filter, category=category_filter, search=search_files)
        st.markdown(f"**عدد الملفات:** {len(files_list)}")
        if not files_list:
            st.info("لا توجد ملفات")
        for f in files_list:
            subj = SUBJECTS.get(f["subject"], {"name": f["subject"] or "عام", "icon": "📄"})
            icon = get_file_icon(f["file_type"], f["file_name"])
            with st.container():
                st.markdown(f"""
                <div class="file-card">
                    <div class="file-icon">{icon}</div>
                    <div class="file-info">
                        <div class="file-title">{f['title']}</div>
                        <div class="file-meta">{subj['icon']} {subj['name']} • {format_size(f['file_size'])} • {f['file_name']}</div>
                        <div class="file-meta">{f['description'] or ''}</div>
                        <div class="file-meta">👤 {f['owner'] or 'مجهول'} • 📅 {f['created_at'][:16]} • ⬇️ {f['downloads']} تحميل</div>
                    </div>
                </div>
                """, unsafe_allow_html=True)
                c1, c2 = st.columns([3, 1])
                with c1:
                    if st.button(f"⬇️ تحميل ({format_size(f['file_size'])})", key=f"dl_file_{f['id']}", use_container_width=True):
                        increment_file_download(f["id"])
                        make_download_button(f["file_path"], f["file_name"], f"dl_btn_{f['id']}", "📥 اضغط للتحميل")
                with c2:
                    if st.session_state.role == "developer" or st.session_state.username == f["owner"]:
                        if st.button("🗑️ حذف", key=f"del_file_{f['id']}", use_container_width=True):
                            delete_file_record(f["id"])
                            st.success("تم الحذف")
                            st.rerun()
                st.divider()
    with tab2:
        st.markdown("### ⬆️ رفع ملف جديد")
        with st.form("upload_file_form"):
            title = st.text_input("عنوان الملف *")
            subject = st.selectbox("المادة", list(SUBJECTS.keys()),
                                   format_func=lambda x: f"{SUBJECTS[x]['icon']} {SUBJECTS[x]['name']}")
            category = st.selectbox("النوع", ["files", "lessons", "exercises", "summaries", "books"],
                                    format_func=lambda x: {
                                        "files": "ملف عام", "lessons": "درس", "exercises": "تمارين",
                                        "summaries": "ملخص", "books": "كتاب"
                                    }.get(x, x))
            description = st.text_area("وصف مختصر")
            uploaded = st.file_uploader("اختر الملف *", type=None)
            if st.form_submit_button("⬆️ رفع الملف", use_container_width=True):
                if not title or not uploaded:
                    st.error("العنوان والملف مطلوبان")
                else:
                    path = upload_file(uploaded, "files")
                    size = os.path.getsize(path) if path and os.path.exists(path) else 0
                    add_file_record(subject, category, title, description, path, uploaded.name, size,
                                    uploaded.type or "", st.session_state.username)
                    st.success(T("file_uploaded") + " ✅")
                    st.rerun()
    footer()

# ============================================================
# EXAM MODELS PAGE (NEW)
# ============================================================

def render_exam_models():
    st.markdown('<div class="header-banner"><h1>📄 نماذج الفروض والامتحانات</h1><p>حمّل نماذج الفروض السابقة للتدريب</p></div>', unsafe_allow_html=True)
    tab1, tab2 = st.tabs(["📥 تصفح النماذج", "⬆️ رفع نموذج"])
    with tab1:
        c1, c2, c3, c4 = st.columns(4)
        with c1:
            subject_filter = st.selectbox("المادة", ["all"] + list(SUBJECTS.keys()),
                                          format_func=lambda x: "الكل" if x == "all" else f"{SUBJECTS[x]['icon']} {SUBJECTS[x]['name']}",
                                          key="models_subject")
        with c2:
            years = get_exam_years()
            year_filter = st.selectbox("السنة", ["all"] + years,
                                       format_func=lambda x: "الكل" if x == "all" else x,
                                       key="models_year")
        with c3:
            semester_filter = st.selectbox("الدورة", ["all", "الأولى", "الثانية"],
                                           format_func=lambda x: "الكل" if x == "all" else f"الدورة {x}",
                                           key="models_semester")
        with c4:
            search_models = st.text_input("🔍 بحث", key="models_search")
        models = get_exam_models(subject=subject_filter, year=year_filter, semester=semester_filter, search=search_models)
        st.markdown(f"**عدد النماذج:** {len(models)}")
        if not models:
            st.info("لا توجد نماذج")
        for m in models:
            subj = SUBJECTS.get(m["subject"], {"name": m["subject"], "icon": "📄"})
            icon = get_file_icon("", m["file_name"])
            with st.container():
                st.markdown(f"""
                <div class="file-card">
                    <div class="file-icon">{icon}</div>
                    <div class="file-info">
                        <div class="file-title">{m['title']}</div>
                        <div class="file-meta">{subj['icon']} {subj['name']} • {m['year'] or '—'} • {m['semester'] or '—'}</div>
                        <div class="file-meta">{m['description'] or ''}</div>
                        <div class="file-meta">👤 {m['owner'] or 'مجهول'} • 📅 {m['created_at'][:16]} • ⬇️ {m['downloads']} تحميل</div>
                    </div>
                </div>
                """, unsafe_allow_html=True)
                c1, c2 = st.columns([3, 1])
                with c1:
                    if st.button(f"⬇️ تحميل ({format_size(m['file_size'])})", key=f"dl_model_{m['id']}", use_container_width=True):
                        increment_exam_download(m["id"])
                        make_download_button(m["file_path"], m["file_name"], f"dl_m_btn_{m['id']}", "📥 اضغط للتحميل")
                with c2:
                    if st.session_state.role == "developer" or st.session_state.username == m["owner"]:
                        if st.button("🗑️ حذف", key=f"del_model_{m['id']}", use_container_width=True):
                            delete_exam_model(m["id"])
                            st.success("تم الحذف")
                            st.rerun()
                st.divider()
    with tab2:
        st.markdown("### ⬆️ رفع نموذج فرض جديد")
        with st.form("upload_model_form"):
            title = st.text_input("عنوان النموذج *")
            subject = st.selectbox("المادة", list(SUBJECTS.keys()),
                                   format_func=lambda x: f"{SUBJECTS[x]['icon']} {SUBJECTS[x]['name']}",
                                   key="model_subject_form")
            c1, c2 = st.columns(2)
            with c1:
                year = st.text_input("السنة (مثال: 2024)")
            with c2:
                semester = st.selectbox("الدورة", ["", "الأولى", "الثانية"],
                                        format_func=lambda x: x if x else "غير محدد")
            description = st.text_area("وصف")
            uploaded = st.file_uploader("اختر ملف النموذج (PDF, Word...)", type=None, key="model_file")
            if st.form_submit_button("⬆️ رفع النموذج", use_container_width=True):
                if not title or not uploaded:
                    st.error("العنوان والملف مطلوبان")
                else:
                    path = upload_file(uploaded, "models")
                    size = os.path.getsize(path) if path and os.path.exists(path) else 0
                    add_exam_model(subject, title, year, semester, description, path, uploaded.name, size,
                                   st.session_state.username)
                    st.success("تم رفع النموذج بنجاح ✅")
                    st.rerun()
    footer()

# ============================================================
# QUIZ
# ============================================================

def _render_quiz_ui(questions, lesson_id):
    total = len(questions)
    start = st.session_state.get("quiz_start_time", time.time())
    elapsed = time.time() - start
    remaining = max(0, 600 - elapsed)
    if remaining <= 0:
        st.error("⏰ انتهى الوقت!")
        if st.button("عرض النتيجة"):
            st.session_state.page = "dashboard"
            st.rerun()
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
                         st.session_state.quiz_lesson_title,
                         st.session_state.quiz_subject,
                         score, total, percent)
        update_user_stats(st.session_state.username, points=score * 10, quiz=True,
                          perfect=(score == total), subject=st.session_state.quiz_subject)
        st.success(f"🎉 نتيجتك: {score}/{total} ({percent:.1f}%)")
        if score == total:
            st.balloons()
        st.markdown("### 📋 التصحيح")
        for i, q in enumerate(questions):
            user_ans = answers.get(i)
            correct = q["correct_answer"]
            icon = "✅" if user_ans == correct else "❌"
            st.markdown(f"{icon} **{q['question']}**")
            st.write(f"إجابتك: {user_ans.upper() if user_ans else '—'} | الصحيحة: {correct.upper()}")
            if q.get("explanation"):
                st.info(q["explanation"])
            st.divider()
        if st.button("العودة للرئيسية"):
            for k in ["quiz_questions", "quiz_answers", "quiz_current", "quiz_start_time"]:
                st.session_state.pop(k, None)
            st.session_state.page = "dashboard"
            st.rerun()
        return
    q = questions[idx]
    st.markdown(f"#### السؤال {idx + 1} / {total}")
    st.write(q["question"])
    options = {
        "a": q["option_a"], "b": q["option_b"],
        "c": q["option_c"], "d": q["option_d"],
    }
    selected = st.radio("اختر:", list(options.keys()),
                        format_func=lambda x: f"{x.upper()}) {options[x]}",
                        index=None, key=f"q_{idx}")
    c1, c2 = st.columns(2)
    with c1:
        if st.button("السابق", disabled=(idx == 0)):
            st.session_state.quiz_current -= 1
            st.rerun()
    with c2:
        if st.button("التالي", disabled=(selected is None)):
            answers[idx] = selected
            st.session_state.quiz_answers = answers
            st.session_state.quiz_current += 1
            st.rerun()

def render_quiz():
    st.markdown('<div class="header-banner"><h1>📝 الاختبار</h1></div>', unsafe_allow_html=True)
    questions = st.session_state.get("quiz_questions", [])
    lesson_id = st.session_state.get("quiz_lesson_id")
    if not questions:
        st.warning("لا توجد أسئلة")
        if st.button("رجوع"):
            st.session_state.page = "lessons"
            st.rerun()
        return
    _render_quiz_ui(questions, lesson_id)
    footer()

def render_quick_review():
    st.markdown('<div class="header-banner"><h1>⚡ مراجعة سريعة</h1></div>', unsafe_allow_html=True)
    subject = st.selectbox("المادة", list(SUBJECTS.keys()),
                           format_func=lambda x: f"{SUBJECTS[x]['icon']} {SUBJECTS[x]['name']}")
    conn = get_db()
    c = conn.cursor()
    c.execute("""SELECT q.*, l.title as lesson_title FROM questions q
                 JOIN lessons l ON q.lesson_id = l.id WHERE l.subject = ? ORDER BY RANDOM() LIMIT 10""", (subject,))
    questions = [dict(r) for r in c.fetchall()]
    conn.close()
    if not questions:
        st.info("لا توجد أسئلة")
        footer()
        return
    if "qr_answers" not in st.session_state or st.session_state.get("qr_subject") != subject:
        st.session_state.qr_answers = {}
        st.session_state.qr_subject = subject
    answers = st.session_state.qr_answers
    for i, q in enumerate(questions):
        st.markdown(f"**{i+1}. {q['question']}**")
        opts = {"a": q["option_a"], "b": q["option_b"], "c": q["option_c"], "d": q["option_d"]}
        choice = st.radio("", list(opts.keys()), format_func=lambda x: f"{x.upper()}) {opts[x]}",
                          index=None, key=f"qr_{i}")
        if choice:
            answers[i] = choice
        st.divider()
    if st.button("✅ تصحيح"):
        score = sum(1 for i, q in enumerate(questions) if answers.get(i) == q["correct_answer"])
        st.success(f"نتيجتك: {score}/{len(questions)}")
    footer()

# ============================================================
# DAILY CHALLENGE
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
    conn.commit()
    conn.close()
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
        st.warning("لا توجد أسئلة في قاعدة البيانات")
        footer()
        return
    if st.session_state.daily_done:
        score = sum(1 for i, q in enumerate(questions) if st.session_state.daily_answers.get(i) == q["correct_answer"])
        st.success(f"🎉 نتيجتك: {score}/{len(questions)}")
        if score == len(questions):
            st.balloons()
        for i, q in enumerate(questions):
            user_ans = st.session_state.daily_answers.get(i)
            correct = q["correct_answer"]
            icon = "✅" if user_ans == correct else "❌"
            st.markdown(f"{icon} {q['question']} — الصحيحة: {correct.upper()}")
        if st.button("تحدي جديد"):
            st.session_state.daily_questions = get_daily_challenge()
            st.session_state.daily_answers = {}
            st.session_state.daily_done = False
            st.rerun()
        footer()
        return
    for i, q in enumerate(questions):
        st.markdown(f"**{i+1}. {q['question']}**")
        opts = {"a": q["option_a"], "b": q["option_b"], "c": q["option_c"], "d": q["option_d"]}
        choice = st.radio("", list(opts.keys()), format_func=lambda x: f"{x.upper()}) {opts[x]}",
                          index=None, key=f"daily_{i}")
        if choice:
            st.session_state.daily_answers[i] = choice
    if st.button("✅ إرسال"):
        score = sum(1 for i, q in enumerate(questions) if st.session_state.daily_answers.get(i) == q["correct_answer"])
        save_daily_challenge(st.session_state.username, score, len(questions))
        st.session_state.daily_done = True
        st.rerun()
    footer()

# ============================================================
# POMODORO
# ============================================================

def render_pomodoro():
    st.markdown("### ⏱️ مؤقت بومودورو")
    st.write("قم بتقسيم وقتك: 25 دقيقة مراجعة + 5 دقائق راحة")
    if "pomodoro_start" not in st.session_state:
        st.session_state.pomodoro_start = None
        st.session_state.pomodoro_duration = 25 * 60
        st.session_state.pomodoro_mode = "work"
    c1, c2, c3 = st.columns(3)
    with c1:
        if st.button("▶️ ابدأ 25 دقيقة"):
            st.session_state.pomodoro_start = time.time()
            st.session_state.pomodoro_duration = 25 * 60
            st.session_state.pomodoro_mode = "work"
            st.rerun()
    with c2:
        if st.button("☕ راحة 5 دقائق"):
            st.session_state.pomodoro_start = time.time()
            st.session_state.pomodoro_duration = 5 * 60
            st.session_state.pomodoro_mode = "break"
            st.rerun()
    with c3:
        if st.button("⏹️ إيقاف"):
            st.session_state.pomodoro_start = None
            st.rerun()
    if st.session_state.pomodoro_start:
        elapsed = time.time() - st.session_state.pomodoro_start
        remaining = max(0, st.session_state.pomodoro_duration - elapsed)
        mins, secs = divmod(int(remaining), 60)
        mode = "🔴 مراجعة" if st.session_state.pomodoro_mode == "work" else "🟢 راحة"
        st.markdown(f"<h1 style='text-align:center;font-size:4rem;'>{mins:02d}:{secs:02d}</h1>", unsafe_allow_html=True)
        st.markdown(f"<p style='text-align:center;'>{mode}</p>", unsafe_allow_html=True)
        progress = 1 - (remaining / st.session_state.pomodoro_duration)
        st.progress(progress)
        if remaining <= 0:
            st.success("انتهى الوقت!")
            st.balloons()
            st.session_state.pomodoro_start = None

def render_pomodoro_page():
    st.markdown('<div class="header-banner"><h1>⏱️ مؤقت المراجعة</h1></div>', unsafe_allow_html=True)
    render_pomodoro()
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
            front = st.text_input("الوجه")
            back = st.text_area("الظهر")
            if st.form_submit_button("إضافة"):
                if front and back:
                    add_flashcard(st.session_state.username, subject, front, back)
                    st.success("تمت الإضافة")
                    st.rerun()
    subject_filter = st.selectbox("تصفية حسب المادة", ["all"] + list(SUBJECTS.keys()),
                                  format_func=lambda x: "الكل" if x == "all" else SUBJECTS[x]["name"])
    cards = get_flashcards(st.session_state.username, subject_filter)
    if not cards:
        st.info("لا توجد بطاقات")
    for card in cards:
        status = "✅" if card["known"] else "❌"
        with st.expander(f"{status} {card['front']}"):
            st.write(card["back"])
            c1, c2 = st.columns(2)
            with c1:
                if st.button("🔄 تبديل", key=f"toggle_{card['id']}"):
                    toggle_flashcard_known(card["id"])
                    st.rerun()
            with c2:
                if st.button("🗑️ حذف", key=f"del_fc_{card['id']}"):
                    delete_flashcard(card["id"])
                    st.rerun()
    footer()

# ============================================================
# STUDY PLAN
# ============================================================

def render_study_plan():
    st.markdown('<div class="header-banner"><h1>📅 خطة الدراسة</h1></div>', unsafe_allow_html=True)
    c1, c2 = st.columns(2)
    with c1:
        if st.button("🔄 توليد تلقائي", use_container_width=True):
            auto_generate_plan(st.session_state.username)
            st.success("تم التوليد")
            st.rerun()
    with c2:
        with st.expander("➕ إضافة مهمة"):
            with st.form("add_plan"):
                subject = st.selectbox("المادة", list(SUBJECTS.keys()),
                                       format_func=lambda x: SUBJECTS[x]["name"])
                priority = st.selectbox("الأولوية", ["high", "medium", "low"],
                                        format_func=lambda x: {"high": "🔴 عالية", "medium": "🟡 متوسطة", "low": "🟢 منخفضة"}[x])
                target = st.date_input("التاريخ المستهدف")
                if st.form_submit_button("إضافة"):
                    add_study_plan(st.session_state.username, subject, priority, target.strftime("%Y-%m-%d"))
                    st.rerun()
    plan = get_study_plan(st.session_state.username)
    if not plan:
        st.info("لا توجد خطة. جرب التوليد التلقائي")
    for p in plan:
        status = "✅" if p["completed"] else "⏳"
        subj_name = SUBJECTS.get(p["subject"], {"name": p["subject"]})["name"]
        st.markdown(f"{status} **{subj_name}** — {p['priority']} — {p['target_date'] or ''}")
        if st.button("تبديل", key=f"toggle_plan_{p['id']}"):
            toggle_study_plan(p["id"])
            st.rerun()
    footer()

# ============================================================
# FRIENDS
# ============================================================

def render_friends():
    st.markdown('<div class="header-banner"><h1>👥 الأصدقاء</h1></div>', unsafe_allow_html=True)
    with st.form("add_friend"):
        fu = st.text_input("اسم المستخدم للصديق")
        if st.form_submit_button("إرسال طلب"):
            if fu and fu != st.session_state.username:
                if add_friend(st.session_state.username, fu):
                    st.success("تم الإرسال")
                else:
                    st.error("موجود مسبقاً")
            st.rerun()
    friends = get_friends(st.session_state.username)
    if not friends:
        st.info("لا أصدقاء بعد")
    for f in friends:
        st.markdown(f"**{f['friend_username']}** — {f['status']}")
        if st.button("إزالة", key=f"rm_friend_{f['id']}"):
            remove_friend(st.session_state.username, f["friend_username"])
            st.rerun()
    footer()

# ============================================================
# LEADERBOARD
# ============================================================

def render_leaderboard():
    st.markdown('<div class="header-banner"><h1>🏆 المتصدرون</h1></div>', unsafe_allow_html=True)
    period = st.radio("الفترة", ["all", "week", "month"], horizontal=True,
                      format_func=lambda x: {"all": "الكل", "week": "الأسبوع", "month": "الشهر"}[x])
    board = get_leaderboard(period)
    if not board:
        st.info("لا بيانات")
    for i, row in enumerate(board):
        medal = ["🥇", "🥈", "🥉"][i] if i < 3 else f"#{i+1}"
        st.markdown(f"{medal} **{row['full_name'] or row['username']}** — {row['pts']} نقطة")
    footer()

# ============================================================
# WEEKLY REPORT
# ============================================================

def render_progress_chart(u):
    history = get_quiz_history(u, 30)
    if not history:
        st.info("لا يوجد سجل بعد")
        return
    data = []
    for h in reversed(list(history)):
        data.append({"date": h["created_at"][:10], "percent": h["percent"]})
    try:
        import pandas as pd
        df = pd.DataFrame(data)
        if not df.empty:
            df = df.groupby("date").mean().reset_index()
            st.line_chart(df.set_index("date")["percent"])
    except ImportError:
        st.info("pandas غير مثبت — عرض بيانات بسيطة")
        for d in data[-10:]:
            st.write(f"{d['date']}: {d['percent']:.1f}%")

def render_weekly_report():
    st.markdown('<div class="header-banner"><h1>📊 التقرير الأسبوعي</h1></div>', unsafe_allow_html=True)
    report = get_weekly_report(st.session_state.username)
    if report:
        c1, c2, c3 = st.columns(3)
        with c1:
            st.metric("الاختبارات", report["cnt"])
        with c2:
            st.metric("مجموع النقاط", report["total_score"])
        with c3:
            st.metric("المعدل", f"{report['avg_pct']:.1f}%")
    st.markdown("### 📈 تطور الأداء")
    render_progress_chart(st.session_state.username)
    st.markdown("### 📊 إحصائيات المواد")
    stats = get_subject_stats(st.session_state.username)
    for s in stats:
        subj = SUBJECTS.get(s["subject"], {"name": s["subject"], "icon": "📖"})
        st.markdown(f"{subj['icon']} **{subj['name']}** — {s['cnt']} اختبار — معدل {s['avg_pct']:.1f}%")
    st.markdown("### ⚠️ نقاط الضعف")
    weak = get_weaknesses(st.session_state.username)
    if weak:
        for w in weak:
            subj = SUBJECTS.get(w["subject"], {"name": w["subject"]})
            st.warning(f"{subj['name']} — معدل {w['avg_pct']:.1f}%")
    else:
        st.success("لا نقاط ضعف واضحة")
    footer()

# ============================================================
# NOTIFICATIONS
# ============================================================

def render_notifications():
    st.markdown('<div class="header-banner"><h1>🔔 الإشعارات</h1></div>', unsafe_allow_html=True)
    notifs = get_notifications(st.session_state.username)
    if not notifs:
        st.info("لا إشعارات")
    for n in notifs:
        icon = n["icon"] or "🔔"
        read = "" if n["is_read"] else "🟢 "
        st.markdown(f"{read}{icon} **{n['title']}** — {n['message']} _({n['created_at'][:16]})_")
    if st.button("تعليم الكل كمقروء"):
        mark_notifications_read(st.session_state.username)
        st.rerun()
    footer()

# ============================================================
# MY STATS
# ============================================================

def get_achievement_progress(u):
    stats = get_user_stats(u)
    if not stats:
        return []
    progress = []
    progress.append({"name": "أول اختبار", "current": min(stats["quizzes_taken"], 1), "target": 1})
    progress.append({"name": "5 اختبارات", "current": min(stats["quizzes_taken"], 5), "target": 5})
    progress.append({"name": "10 اختبارات", "current": min(stats["quizzes_taken"], 10), "target": 10})
    progress.append({"name": "25 اختبار", "current": min(stats["quizzes_taken"], 25), "target": 25})
    progress.append({"name": "50 اختبار", "current": min(stats["quizzes_taken"], 50), "target": 50})
    progress.append({"name": "المستوى 5", "current": min(stats["level"], 5), "target": 5})
    progress.append({"name": "المستوى 10", "current": min(stats["level"], 10), "target": 10})
    progress.append({"name": "المستوى 20", "current": min(stats["level"], 20), "target": 20})
    progress.append({"name": "7 مواد", "current": min(stats["unique_subjects"], 7), "target": 7})
    progress.append({"name": "سلسلة 7 أيام", "current": min(stats["streak"], 7), "target": 7})
    return progress

def get_recommendations(u):
    conn = get_db()
    c = conn.cursor()
    recs = []
    c.execute("""SELECT subject, AVG(percent) as avg_pct FROM quiz_history
                 WHERE username = ? GROUP BY subject ORDER BY avg_pct ASC LIMIT 3""", (u,))
    weak_subjects = c.fetchall()
    for w in weak_subjects:
        if w["avg_pct"] < 70:
            subj = SUBJECTS.get(w["subject"], {"name": w["subject"], "icon": "📖"})
            recs.append({
                "type": "weakness",
                "subject": w["subject"],
                "title": f"راجع {subj['icon']} {subj['name']}",
                "desc": f"معدلك {w['avg_pct']:.0f}% — يحتاج تحسين",
                "icon": "⚠️"
            })
    c.execute("""SELECT l.* FROM lessons l
                 LEFT JOIN quiz_history q ON l.id = q.lesson_id AND q.username = ?
                 WHERE q.id IS NULL LIMIT 3""", (u,))
    unread_lessons = c.fetchall()
    for l in unread_lessons:
        subj = SUBJECTS.get(l["subject"], {"name": l["subject"], "icon": "📖"})
        recs.append({
            "type": "new",
            "subject": l["subject"],
            "title": f"جرب درس: {l['title']}",
            "desc": f"{subj['icon']} {subj['name']} — لم تجربه بعد",
            "icon": "🆕"
        })
    conn.close()
    return recs[:5]

def render_achievement_tracker():
    st.markdown("### 🎯 تتبع الإنجازات")
    progress = get_achievement_progress(st.session_state.username)
    for p in progress:
        pct = p["current"] / p["target"] if p["target"] else 0
        st.markdown(f"**{p['name']}** — {p['current']}/{p['target']}")
        st.progress(min(pct, 1.0))

def render_my_stats():
    st.markdown('<div class="header-banner"><h1>📈 إحصائياتي</h1></div>', unsafe_allow_html=True)
    stats = get_user_stats(st.session_state.username)
    if stats:
        c1, c2, c3, c4 = st.columns(4)
        with c1:
            st.metric("النقاط", stats["total_points"])
        with c2:
            st.metric("المستوى", stats["level"])
        with c3:
            st.metric("الاختبارات", stats["quizzes_taken"])
        with c4:
            st.metric("العلامات الكاملة", stats["perfect_scores"])
        st.markdown(f"**اللقب:** {get_rank(stats['level'])}")
        st.markdown(f"**السلسلة:** {stats['streak']} يوم")
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
    history = get_quiz_history(st.session_state.username, 20)
    for h in history:
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
    if not favs:
        st.info("لا توجد دروس مفضلة")
    for lesson in favs:
        _render_lesson_card(lesson)
        st.divider()
    footer()

# ============================================================
# DEVELOPER PANEL
# ============================================================

def render_developer_panel():
    st.markdown('<div class="header-banner"><h1>🛠️ لوحة المطور</h1></div>', unsafe_allow_html=True)
    tab1, tab2, tab3, tab4, tab5 = st.tabs(["📚 الدروس", "❓ الأسئلة", "👥 المستخدمون", "📂 الملفات", "📄 نماذج الفروض"])
    with tab1:
        with st.expander("➕ إضافة درس"):
            with st.form("add_lesson_form"):
                subject = st.selectbox("المادة", list(SUBJECTS.keys()),
                                       format_func=lambda x: f"{SUBJECTS[x]['icon']} {SUBJECTS[x]['name']}")
                language = st.selectbox("اللغة", ["ar", "fr", "en"])
                title = st.text_input("العنوان")
                content = st.text_area("المحتوى")
                image_url = st.text_input("رابط الصورة")
                pdf_file = st.file_uploader("رفع PDF", type=["pdf"])
                if st.form_submit_button("إضافة الدرس"):
                    pdf_path = None
                    if pdf_file:
                        pdf_path = upload_file(pdf_file, "pdfs")
                    if title:
                        add_lesson(subject, language, title, content, image_url, pdf_path, st.session_state.username)
                        st.success("تمت الإضافة")
                        st.rerun()
        lessons = load_lessons()
        st.markdown(f"**إجمالي الدروس:** {len(lessons)}")
        for lesson in lessons:
            with st.expander(f"{SUBJECTS.get(lesson['subject'], {'icon':'📖'})['icon']} {lesson['title']}"):
                st.write(lesson["content"])
                if st.button("🗑️ حذف", key=f"del_lesson_{lesson['id']}"):
                    delete_lesson(lesson["id"])
                    st.rerun()
    with tab2:
        with st.expander("➕ إضافة سؤال"):
            lessons = load_lessons()
            if lessons:
                with st.form("add_question_form"):
                    lesson_options = {l["id"]: f"{l['title']} ({l['subject']})" for l in lessons}
                    lid = st.selectbox("الدرس", list(lesson_options.keys()),
                                       format_func=lambda x: lesson_options[x])
                    question = st.text_input("السؤال")
                    a = st.text_input("الخيار أ")
                    b = st.text_input("الخيار ب")
                    c_opt = st.text_input("الخيار ج")
                    d = st.text_input("الخيار د")
                    correct = st.selectbox("الإجابة الصحيحة", ["a", "b", "c", "d"])
                    explanation = st.text_area("الشرح")
                    if st.form_submit_button("إضافة السؤال"):
                        if question and a and b and c_opt and d:
                            add_question(lid, question, a, b, c_opt, d, correct, explanation)
                            st.success("تمت الإضافة")
                            st.rerun()
        lessons = load_lessons()
        for lesson in lessons:
            questions = load_questions(lesson["id"])
            if questions:
                st.markdown(f"**{lesson['title']}** ({len(questions)} أسئلة)")
                for q in questions:
                    with st.expander(q["question"]):
                        st.write(f"أ) {q['option_a']}")
                        st.write(f"ب) {q['option_b']}")
                        st.write(f"ج) {q['option_c']}")
                        st.write(f"د) {q['option_d']}")
                        st.success(f"الإجابة: {q['correct_answer']}")
                        if q["explanation"]:
                            st.info(q["explanation"])
                        if st.button("🗑️ حذف", key=f"del_q_{q['id']}"):
                            delete_question(q["id"])
                            st.rerun()
    with tab3:
        conn = get_db()
        c = conn.cursor()
        c.execute("SELECT * FROM users ORDER BY created_at DESC")
        users = c.fetchall()
        conn.close()
        st.markdown(f"**إجمالي المستخدمين:** {len(users)}")
        for user in users:
            st.markdown(f"**{user['username']}** — {user['full_name']} — {user['role']} — {user['created_at'][:10]}")
    with tab4:
        st.markdown("### 📂 إدارة الملفات")
        st.markdown("#### ⬆️ رفع ملف جديد")
        with st.form("dev_upload_file"):
            title = st.text_input("عنوان الملف *")
            subject = st.selectbox("المادة", list(SUBJECTS.keys()),
                                   format_func=lambda x: f"{SUBJECTS[x]['icon']} {SUBJECTS[x]['name']}",
                                   key="dev_file_subject")
            category = st.selectbox("النوع", ["files", "lessons", "exercises", "summaries", "books"],
                                    format_func=lambda x: {
                                        "files": "ملف عام", "lessons": "درس", "exercises": "تمارين",
                                        "summaries": "ملخص", "books": "كتاب"
                                    }.get(x, x), key="dev_file_cat")
            description = st.text_area("وصف مختصر", key="dev_file_desc")
            uploaded = st.file_uploader("اختر الملف *", type=None, key="dev_file_upload")
            if st.form_submit_button("⬆️ رفع الملف", use_container_width=True):
                if not title or not uploaded:
                    st.error("العنوان والملف مطلوبان")
                else:
                    path = upload_file(uploaded, "files")
                    size = os.path.getsize(path) if path and os.path.exists(path) else 0
                    add_file_record(subject, category, title, description, path, uploaded.name, size,
                                    uploaded.type or "", st.session_state.username)
                    st.success(T("file_uploaded") + " ✅")
                    st.rerun()
        st.markdown("#### 📋 قائمة الملفات")
        all_files = get_files()
        st.markdown(f"**إجمالي الملفات:** {len(all_files)}")
        for f in all_files:
            subj = SUBJECTS.get(f["subject"], {"name": f["subject"] or "عام", "icon": "📄"})
            icon = get_file_icon(f["file_type"], f["file_name"])
            with st.expander(f"{icon} {f['title']} — {subj['name']}"):
                st.write(f"**الملف:** {f['file_name']}")
                st.write(f"**الحجم:** {format_size(f['file_size'])}")
                st.write(f"**النوع:** {f['file_type'] or 'غير محدد'}")
                st.write(f"**الوصف:** {f['description'] or '—'}")
                st.write(f"**رافع:** {f['owner']}")
                st.write(f"**التاريخ:** {f['created_at'][:16]}")
                st.write(f"**التحميلات:** {f['downloads']}")
                c1, c2 = st.columns(2)
                with c1:
                    make_download_button(f["file_path"], f["file_name"], f"dev_dl_{f['id']}", "📥 تحميل")
                with c2:
                    if st.button("🗑️ حذف", key=f"dev_del_file_{f['id']}"):
                        delete_file_record(f["id"])
                        st.success("تم الحذف")
                        st.rerun()
    with tab5:
        st.markdown("### 📄 إدارة نماذج الفروض")
        st.markdown("#### ⬆️ رفع نموذج جديد")
        with st.form("dev_upload_model"):
            title = st.text_input("عنوان النموذج *", key="dev_model_title")
            subject = st.selectbox("المادة", list(SUBJECTS.keys()),
                                   format_func=lambda x: f"{SUBJECTS[x]['icon']} {SUBJECTS[x]['name']}",
                                   key="dev_model_subject")
            c1, c2 = st.columns(2)
            with c1:
                year = st.text_input("السنة", key="dev_model_year")
            with c2:
                semester = st.selectbox("الدورة", ["", "الأولى", "الثانية"],
                                        format_func=lambda x: x if x else "غير محدد", key="dev_model_sem")
            description = st.text_area("وصف", key="dev_model_desc")
            uploaded = st.file_uploader("اختر ملف النموذج", type=None, key="dev_model_file")
            if st.form_submit_button("⬆️ رفع النموذج", use_container_width=True):
                if not title or not uploaded:
                    st.error("العنوان والملف مطلوبان")
                else:
                    path = upload_file(uploaded, "models")
                    size = os.path.getsize(path) if path and os.path.exists(path) else 0
                    add_exam_model(subject, title, year, semester, description, path, uploaded.name, size,
                                   st.session_state.username)
                    st.success("تم رفع النموذج بنجاح ✅")
                    st.rerun()
        st.markdown("#### 📋 قائمة النماذج")
        all_models = get_exam_models()
        st.markdown(f"**إجمالي النماذج:** {len(all_models)}")
        for m in all_models:
            subj = SUBJECTS.get(m["subject"], {"name": m["subject"], "icon": "📄"})
            icon = get_file_icon("", m["file_name"])
            with st.expander(f"{icon} {m['title']} — {subj['name']}"):
                st.write(f"**الملف:** {m['file_name']}")
                st.write(f"**الحجم:** {format_size(m['file_size'])}")
                st.write(f"**السنة:** {m['year'] or '—'}")
                st.write(f"**الدورة:** {m['semester'] or '—'}")
                st.write(f"**الوصف:** {m['description'] or '—'}")
                st.write(f"**رافع:** {m['owner']}")
                st.write(f"**التاريخ:** {m['created_at'][:16]}")
                st.write(f"**التحميلات:** {m['downloads']}")
                c1, c2 = st.columns(2)
                with c1:
                    make_download_button(m["file_path"], m["file_name"], f"dev_dl_m_{m['id']}", "📥 تحميل")
                with c2:
                    if st.button("🗑️ حذف", key=f"dev_del_model_{m['id']}"):
                        delete_exam_model(m["id"])
                        st.success("تم الحذف")
                        st.rerun()
    footer()

# ============================================================
# SIDEBAR
# ============================================================

def render_sidebar():
    with st.sidebar:
        st.markdown(f"### 👤 {st.session_state.full_name or st.session_state.username}")
        stats = get_user_stats(st.session_state.username)
        if stats:
            st.markdown(f"**{get_rank(stats['level'])}** — المستوى {stats['level']}")
            st.progress((stats["total_points"] % 100) / 100)
        theme_keys = list(THEMES.keys())
        theme_names = [THEMES[k]["name"] for k in theme_keys]
        current_theme = st.session_state.get("theme", "fcb")
        theme_idx = theme_keys.index(current_theme) if current_theme in theme_keys else 0
        selected_theme = st.selectbox("🎨 الثيم", theme_names, index=theme_idx)
        st.session_state.theme = theme_keys[theme_names.index(selected_theme)]
        lang_options = ["ar", "fr", "en"]
        lang_names = ["العربية", "Français", "English"]
        current_lang = st.session_state.get("language", "ar")
        lang_idx = lang_options.index(current_lang) if current_lang in lang_options else 0
        selected_lang = st.selectbox("🌐 اللغة", lang_names, index=lang_idx)
        st.session_state.language = lang_options[lang_names.index(selected_lang)]
        st.divider()
        pages = [
            ("dashboard", "🏠", T("home")),
            ("lessons", "📖", T("lessons")),
            ("files", "📂", "الملفات"),
            ("exam_models", "📄", "نماذج الفروض"),
            ("daily_challenge", "🎯", "التحدي اليومي"),
            ("quick_review", "⚡", T("quick_review")),
            ("pomodoro", "⏱️", "مؤقت المراجعة"),
            ("flashcards", "🃏", T("flashcards")),
            ("study_plan", "📅", T("study_plan")),
            ("friends", "👥", T("friends")),
            ("leaderboard", "🏆", T("leaderboard")),
            ("weekly_report", "📊", T("weekly_report")),
            ("notifications", "🔔", T("notifications")),
            ("my_stats", "📈", T("my_stats")),
            ("favorites", "❤️", T("favorites")),
        ]
        if st.session_state.role == "developer":
            pages.append(("developer_panel", "🛠️", T("developer")))
        for page_key, icon, label in pages:
            if st.button(f"{icon} {label}", key=f"nav_{page_key}", use_container_width=True):
                st.session_state.page = page_key
                st.rerun()
        st.divider()
        unread = get_notifications(st.session_state.username, unread=True)
        if unread:
            st.info(f"🔔 لديك {len(unread)} إشعارات جديدة")
        if st.button(f"🚪 {T('logout')}", use_container_width=True):
            for key in list(st.session_state.keys()):
                del st.session_state[key]
            st.rerun()

# ============================================================
# MAIN
# ============================================================

init_db()

if "theme" not in st.session_state:
    st.session_state.theme = "fcb"
if "language" not in st.session_state:
    st.session_state.language = "ar"
if "authenticated" not in st.session_state:
    st.session_state.authenticated = False
if "page" not in st.session_state:
    st.session_state.page = "dashboard"

st.set_page_config(page_title="3AC RevisioMaroc", page_icon="📚", layout="wide")
apply_theme()

if not st.session_state.authenticated:
    render_auth_page()
    st.stop()

render_sidebar()

page = st.session_state.get("page", "dashboard")
if page == "dashboard":
    render_dashboard()
elif page == "lessons":
    render_lessons()
elif page == "files":
    render_files()
elif page == "exam_models":
    render_exam_models()
elif page == "quiz":
    render_quiz()
elif page == "daily_challenge":
    render_daily_challenge()
elif page == "pomodoro":
    render_pomodoro_page()
elif page == "quick_review":
    render_quick_review()
elif page == "flashcards":
    render_flashcards()
elif page == "study_plan":
    render_study_plan()
elif page == "friends":
    render_friends()
elif page == "leaderboard":
    render_leaderboard()
elif page == "weekly_report":
    render_weekly_report()
elif page == "notifications":
    render_notifications()
elif page == "my_stats":
    render_my_stats()
elif page == "favorites":
    render_favorites()
elif page == "developer_panel":
    if st.session_state.role == "developer":
        render_developer_panel()
    else:
        st.error("غير مصرح")
else:
    render_dashboard()
