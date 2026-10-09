# ============================================================================
# 3AC RevisioMaroc - النسخة المطورة الكاملة
# © 2026 Soufiane Ouhazza - All Rights Reserved
# ============================================================================

import streamlit as st
import hashlib
import sqlite3
import os
import base64
import random
import time
from datetime import datetime, timedelta
from pathlib import Path

st.set_page_config(
    page_title="3AC RevisioMaroc",
    page_icon="🎓",
    layout="wide",
    initial_sidebar_state="expanded"
)

DB_PATH = "revisiomaroc.db"
UPLOAD_DIR = Path("uploads")
UPLOAD_DIR.mkdir(exist_ok=True)

def get_db():
    conn = sqlite3.connect(DB_PATH, check_same_thread=False)
    conn.row_factory = sqlite3.Row
    return conn

def init_db():
    conn = get_db()
    c = conn.cursor()

    c.execute("""
        CREATE TABLE IF NOT EXISTS users (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            username TEXT UNIQUE NOT NULL,
            password_hash TEXT NOT NULL,
            role TEXT NOT NULL DEFAULT 'student',
            full_name TEXT,
            created_at TEXT DEFAULT CURRENT_TIMESTAMP
        )
    """)

    c.execute("""
        CREATE TABLE IF NOT EXISTS lessons (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            subject TEXT NOT NULL,
            language TEXT NOT NULL,
            title TEXT NOT NULL,
            content TEXT,
            image_url TEXT,
            pdf_url TEXT,
            owner TEXT NOT NULL DEFAULT 'public',
            created_at TEXT DEFAULT CURRENT_TIMESTAMP
        )
    """)

    c.execute("""
        CREATE TABLE IF NOT EXISTS questions (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            lesson_id TEXT NOT NULL,
            question TEXT NOT NULL,
            option_a TEXT NOT NULL,
            option_b TEXT NOT NULL,
            option_c TEXT NOT NULL,
            option_d TEXT NOT NULL,
            correct_answer TEXT NOT NULL,
            explanation TEXT,
            created_at TEXT DEFAULT CURRENT_TIMESTAMP
        )
    """)

    c.execute("""
        CREATE TABLE IF NOT EXISTS quiz_history (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            username TEXT NOT NULL,
            lesson_id TEXT NOT NULL,
            lesson_title TEXT,
            subject TEXT,
            score INTEGER,
            total INTEGER,
            percent REAL,
            created_at TEXT DEFAULT CURRENT_TIMESTAMP
        )
    """)

    c.execute("""
        CREATE TABLE IF NOT EXISTS favorites (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            username TEXT NOT NULL,
            lesson_id INTEGER NOT NULL,
            created_at TEXT DEFAULT CURRENT_TIMESTAMP,
            UNIQUE(username, lesson_id)
        )
    """)

    c.execute("""
        CREATE TABLE IF NOT EXISTS user_stats (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            username TEXT UNIQUE NOT NULL,
            total_points INTEGER DEFAULT 0,
            level INTEGER DEFAULT 1,
            quizzes_taken INTEGER DEFAULT 0,
            perfect_scores INTEGER DEFAULT 0,
            unique_subjects TEXT DEFAULT '',
            badges TEXT DEFAULT '',
            last_daily TEXT,
            streak INTEGER DEFAULT 0
        )
    """)

    c.execute("SELECT * FROM users WHERE username = ?", ("soufianeDEV",))
    if not c.fetchone():
        dev_hash = hashlib.sha256("soufiane2030".encode()).hexdigest()
        c.execute(
            "INSERT INTO users (username, password_hash, role, full_name) VALUES (?, ?, ?, ?)",
            ("soufianeDEV", dev_hash, "developer", "Soufiane Ouhazza")
        )

    conn.commit()
    conn.close()

init_db()

# ----------------------------------------------------------------------------
# دوال مساعدة
# ----------------------------------------------------------------------------
def hash_password(password):
    return hashlib.sha256(password.encode()).hexdigest()

def register_user(username, password, full_name=""):
    if len(password) < 4:
        return False, "❌ كلمة المرور قصيرة جداً (4 أحرف على الأقل)"
    try:
        conn = get_db()
        c = conn.cursor()
        c.execute("SELECT username FROM users WHERE username = ?", (username,))
        if c.fetchone():
            conn.close()
            return False, "❌ اسم المستخدم موجود مسبقاً"

        c.execute(
            "INSERT INTO users (username, password_hash, role, full_name) VALUES (?, ?, ?, ?)",
            (username, hash_password(password), "student", full_name or username)
        )
        c.execute("INSERT OR IGNORE INTO user_stats (username) VALUES (?)", (username,))
        conn.commit()
        conn.close()
        return True, "✅ تم إنشاء الحساب بنجاح"
    except Exception as e:
        return False, f"❌ خطأ: {e}"

def authenticate(username, password):
    try:
        conn = get_db()
        c = conn.cursor()
        c.execute("SELECT * FROM users WHERE username = ?", (username,))
        row = c.fetchone()
        conn.close()
        if not row:
            return False, None
        if row["password_hash"] == hash_password(password):
            return True, {
                "role": row["role"],
                "full_name": row["full_name"] or username
            }
        return False, None
    except Exception as e:
        st.error(f"❌ خطأ في المصادقة: {e}")
        return False, None

# ----------------------------------------------------------------------------
# إحصائيات المستخدم
# ----------------------------------------------------------------------------
def get_user_stats(username):
    try:
        conn = get_db()
        c = conn.cursor()
        c.execute("SELECT * FROM user_stats WHERE username = ?", (username,))
        row = c.fetchone()
        if not row:
            c.execute("INSERT INTO user_stats (username) VALUES (?)", (username,))
            conn.commit()
            c.execute("SELECT * FROM user_stats WHERE username = ?", (username,))
            row = c.fetchone()
        conn.close()
        return dict(row) if row else {}
    except Exception:
        return {}

def update_user_stats(username, points=0, quiz_taken=False, perfect=False, subject=None):
    try:
        conn = get_db()
        c = conn.cursor()
        c.execute("SELECT * FROM user_stats WHERE username = ?", (username,))
        row = c.fetchone()
        if not row:
            c.execute("INSERT INTO user_stats (username) VALUES (?)", (username,))
            conn.commit()
            c.execute("SELECT * FROM user_stats WHERE username = ?", (username,))
            row = c.fetchone()

        total_points = row["total_points"] + points
        level = total_points // 100 + 1
        quizzes = row["quizzes_taken"] + (1 if quiz_taken else 0)
        perfects = row["perfect_scores"] + (1 if perfect else 0)

        subjects = set(filter(None, (row["unique_subjects"] or "").split(",")))
        if subject:
            subjects.add(subject)
        subjects_str = ",".join(subjects)

        c.execute("""
            UPDATE user_stats 
            SET total_points = ?, level = ?, quizzes_taken = ?, 
                perfect_scores = ?, unique_subjects = ?
            WHERE username = ?
        """, (total_points, level, quizzes, perfects, subjects_str, username))
        conn.commit()
        conn.close()
        check_badges(username)
    except Exception as e:
        st.error(f"خطأ فـ تحديث الإحصائيات: {e}")

def save_quiz_result(username, lesson_id, lesson_title, subject, score, total):
    try:
        percent = (score / total * 100) if total > 0 else 0
        conn = get_db()
        c = conn.cursor()
        c.execute("""
            INSERT INTO quiz_history (username, lesson_id, lesson_title, subject, score, total, percent)
            VALUES (?, ?, ?, ?, ?, ?, ?)
        """, (username, str(lesson_id), lesson_title, subject, score, total, percent))
        conn.commit()
        conn.close()
    except Exception as e:
        st.error(f"خطأ فـ حفظ النتيجة: {e}")

def get_quiz_history(username, limit=10):
    try:
        conn = get_db()
        c = conn.cursor()
        c.execute("""
            SELECT * FROM quiz_history WHERE username = ?
            ORDER BY created_at DESC LIMIT ?
        """, (username, limit))
        rows = [dict(r) for r in c.fetchall()]
        conn.close()
        return rows
    except Exception:
        return []

def get_subject_stats(username):
    try:
        conn = get_db()
        c = conn.cursor()
        c.execute("""
            SELECT subject, 
                   COUNT(*) as attempts, 
                   AVG(percent) as avg_percent,
                   MAX(percent) as best_percent
            FROM quiz_history WHERE username = ?
            GROUP BY subject
        """, (username,))
        rows = [dict(r) for r in c.fetchall()]
        conn.close()
        return rows
    except Exception:
        return []

# ----------------------------------------------------------------------------
# نظام الإنجازات
# ----------------------------------------------------------------------------
BADGES = {
    "first_quiz": {"icon": "🎯", "name": "أول اختبار", "desc": "أكملت أول اختبار"},
    "perfect": {"icon": "💯", "name": "العلامة الكاملة", "desc": "100% فـ اختبار"},
    "5_quizzes": {"icon": "🔥", "name": "مجتهد", "desc": "أكملت 5 اختبارات"},
    "10_quizzes": {"icon": "💪", "name": "مثابر", "desc": "أكملت 10 اختبارات"},
    "25_quizzes": {"icon": "🏃", "name": "عدّاء", "desc": "أكملت 25 اختبار"},
    "50_quizzes": {"icon": "🚀", "name": "صاروخ", "desc": "أكملت 50 اختبار"},
    "level_5": {"icon": "⭐", "name": "نجم", "desc": "وصلت للمستوى 5"},
    "level_10": {"icon": "🌟", "name": "نجم لامع", "desc": "وصلت للمستوى 10"},
    "level_20": {"icon": "👑", "name": "ملك", "desc": "وصلت للمستوى 20"},
    "all_subjects": {"icon": "🎓", "name": "الموسوعي", "desc": "جربت كل المواد"},
}

def check_badges(username):
    try:
        stats = get_user_stats(username)
        if not stats:
            return
        current_badges = set(filter(None, (stats.get("badges") or "").split(",")))
        new_badges = set()

        if stats["quizzes_taken"] >= 1: new_badges.add("first_quiz")
        if stats["perfect_scores"] >= 1: new_badges.add("perfect")
        if stats["quizzes_taken"] >= 5: new_badges.add("5_quizzes")
        if stats["quizzes_taken"] >= 10: new_badges.add("10_quizzes")
        if stats["quizzes_taken"] >= 25: new_badges.add("25_quizzes")
        if stats["quizzes_taken"] >= 50: new_badges.add("50_quizzes")
        if stats["level"] >= 5: new_badges.add("level_5")
        if stats["level"] >= 10: new_badges.add("level_10")
        if stats["level"] >= 20: new_badges.add("level_20")
        if len(set(filter(None, (stats.get("unique_subjects") or "").split(",")))) >= len(SUBJECTS):
            new_badges.add("all_subjects")

        all_badges = current_badges | new_badges
        if all_badges != current_badges:
            conn = get_db()
            c = conn.cursor()
            c.execute("UPDATE user_stats SET badges = ? WHERE username = ?",
                      (",".join(all_badges), username))
            conn.commit()
            conn.close()
            for b in (new_badges - current_badges):
                if b in BADGES:
                    st.toast(f"{BADGES[b]['icon']} إنجاز جديد: {BADGES[b]['name']}!", icon="🏆")
    except Exception:
        pass

def get_user_badges(username):
    stats = get_user_stats(username)
    badges = set(filter(None, (stats.get("badges") or "").split(",")))
    return [BADGES[b] for b in badges if b in BADGES]

# ----------------------------------------------------------------------------
# نظام المستويات والألقاب
# ----------------------------------------------------------------------------
RANKS = [
    (1, "🌱 مبتدئ"),
    (3, "📖 متعلّم"),
    (5, "🎯 مجتهد"),
    (8, "⭐ متميز"),
    (12, "🏅 متفوق"),
    (20, "👑 خبير"),
    (35, "🏆 أسطورة"),
    (50, "🌟 أسطورة حية"),
]

def get_rank(level):
    rank = RANKS[0][1]
    for lvl, name in RANKS:
        if level >= lvl:
            rank = name
    return rank

# ----------------------------------------------------------------------------
# المفضلة
# ----------------------------------------------------------------------------
def toggle_favorite(username, lesson_id):
    try:
        conn = get_db()
        c = conn.cursor()
        c.execute("SELECT id FROM favorites WHERE username = ? AND lesson_id = ?",
                  (username, lesson_id))
        if c.fetchone():
            c.execute("DELETE FROM favorites WHERE username = ? AND lesson_id = ?",
                      (username, lesson_id))
            result = False
        else:
            c.execute("INSERT INTO favorites (username, lesson_id) VALUES (?, ?)",
                      (username, lesson_id))
            result = True
        conn.commit()
        conn.close()
        return result
    except Exception:
        return False

def is_favorite(username, lesson_id):
    try:
        conn = get_db()
        c = conn.cursor()
        c.execute("SELECT id FROM favorites WHERE username = ? AND lesson_id = ?",
                  (username, lesson_id))
        result = c.fetchone() is not None
        conn.close()
        return result
    except Exception:
        return False

def get_favorites(username):
    try:
        conn = get_db()
        c = conn.cursor()
        c.execute("""
            SELECT l.* FROM lessons l
            INNER JOIN favorites f ON l.id = f.lesson_id
            WHERE f.username = ?
            ORDER BY f.created_at DESC
        """, (username,))
        rows = [dict(r) for r in c.fetchall()]
        conn.close()
        return rows
    except Exception:
        return []

# ----------------------------------------------------------------------------
# التحدي اليومي
# ----------------------------------------------------------------------------
def check_daily_bonus(username):
    try:
        conn = get_db()
        c = conn.cursor()
        c.execute("SELECT last_daily, streak FROM user_stats WHERE username = ?", (username,))
        row = c.fetchone()
        if not row:
            conn.close()
            return 0

        today = datetime.now().strftime("%Y-%m-%d")
        last = row["last_daily"]
        streak = row["streak"] or 0

        if last == today:
            conn.close()
            return 0

        yesterday = (datetime.now() - timedelta(days=1)).strftime("%Y-%m-%d")
        if last == yesterday:
            streak += 1
        else:
            streak = 1

        bonus = 10 + (streak - 1) * 5
        bonus = min(bonus, 50)

        c.execute("""
            UPDATE user_stats 
            SET last_daily = ?, streak = ?, total_points = total_points + ?
            WHERE username = ?
        """, (today, streak, bonus, username))
        conn.commit()
        conn.close()
        return bonus
    except Exception:
        return 0

# ----------------------------------------------------------------------------
# إدارة الدروس والأسئلة (كما كان)
# ----------------------------------------------------------------------------
def load_lessons(subject=None, language=None, owner=None, search=None):
    try:
        conn = get_db()
        c = conn.cursor()
        query = "SELECT * FROM lessons WHERE 1=1"
        params = []
        if subject:
            query += " AND subject = ?"
            params.append(subject)
        if language:
            query += " AND language = ?"
            params.append(language)
        if owner is not None:
            query += " AND owner = ?"
            params.append(owner)
        if search:
            query += " AND (title LIKE ? OR content LIKE ?)"
            params.extend([f"%{search}%", f"%{search}%"])
        query += " ORDER BY created_at DESC"
        c.execute(query, params)
        rows = [dict(r) for r in c.fetchall()]
        conn.close()
        return rows
    except Exception as e:
        st.error(f"❌ خطأ: {e}")
        return []

def add_lesson(subject, language, title, content, image_url=None, pdf_url=None, owner="public"):
    try:
        conn = get_db()
        c = conn.cursor()
        c.execute(
            "INSERT INTO lessons (subject, language, title, content, image_url, pdf_url, owner) VALUES (?, ?, ?, ?, ?, ?, ?)",
            (subject, language, title, content, image_url, pdf_url, owner)
        )
        conn.commit()
        conn.close()
        return True, "✅ تم الحفظ"
    except Exception as e:
        return False, f"❌ خطأ: {e}"

def delete_lesson(lesson_id, owner_filter=None):
    try:
        conn = get_db()
        c = conn.cursor()
        if owner_filter:
            c.execute("DELETE FROM lessons WHERE id = ? AND owner = ?", (lesson_id, owner_filter))
        else:
            c.execute("DELETE FROM lessons WHERE id = ?", (lesson_id,))
        conn.commit()
        conn.close()
        return True
    except Exception:
        return False

def load_questions(lesson_id):
    try:
        conn = get_db()
        c = conn.cursor()
        c.execute("SELECT * FROM questions WHERE lesson_id = ?", (str(lesson_id),))
        rows = c.fetchall()
        conn.close()
        questions = []
        for q in rows:
            questions.append({
                "id": q["id"],
                "question": q["question"],
                "options": [q["option_a"], q["option_b"], q["option_c"], q["option_d"]],
                "correct": ord(q["correct_answer"]) - 65,
                "explanation": q["explanation"] or ""
            })
        return questions
    except Exception as e:
        st.error(f"❌ خطأ: {e}")
        return []

def add_question(lesson_id, question, opt_a, opt_b, opt_c, opt_d, correct_letter, explanation=""):
    try:
        conn = get_db()
        c = conn.cursor()
        c.execute(
            "INSERT INTO questions (lesson_id, question, option_a, option_b, option_c, option_d, correct_answer, explanation) VALUES (?, ?, ?, ?, ?, ?, ?, ?)",
            (str(lesson_id), question, opt_a, opt_b, opt_c, opt_d, correct_letter, explanation)
        )
        conn.commit()
        conn.close()
        return True, "✅ تم الحفظ"
    except Exception as e:
        return False, f"❌ خطأ: {e}"

def delete_question(question_id):
    try:
        conn = get_db()
        c = conn.cursor()
        c.execute("DELETE FROM questions WHERE id = ?", (question_id,))
        conn.commit()
        conn.close()
        return True
    except Exception:
        return False

def upload_file(uploaded_file, folder="uploads"):
    if uploaded_file is None:
        return None
    try:
        folder_path = UPLOAD_DIR / folder
        folder_path.mkdir(parents=True, exist_ok=True)
        timestamp = int(datetime.now().timestamp() * 1000)
        safe_name = "".join(c for c in uploaded_file.name if c.isalnum() or c in "._-")
        filename = f"{timestamp}_{safe_name}"
        filepath = folder_path / filename
        with open(filepath, "wb") as f:
            f.write(uploaded_file.getbuffer())
        return str(filepath)
    except Exception as e:
        st.error(f"❌ خطأ: {e}")
        return None

def render_pdf(pdf_path):
    try:
        if not os.path.exists(pdf_path):
            st.error("❌ الملف ما كاينش")
            return
        with open(pdf_path, "rb") as f:
            base64_pdf = base64.b64encode(f.read()).decode('utf-8')
        pdf_display = f'<iframe src="data:application/pdf;base64,{base64_pdf}" width="100%" height="600" type="application/pdf" style="border-radius:10px;"></iframe>'
        st.markdown(pdf_display, unsafe_allow_html=True)
    except Exception as e:
        st.error(f"تعذر عرض PDF: {e}")

# ----------------------------------------------------------------------------
# الترجمات
# ----------------------------------------------------------------------------
TRANSLATIONS = {
    "ar": {
        "app_name": "منصة المراجعة الشاملة",
        "dashboard": "🏠 الرئيسية", "lessons": "📚 الدروس", "quizzes": "📝 الاختبارات",
        "developer": "⚙️ لوحة المطور", "my_stats": "📊 إحصائياتي",
        "favorites": "⭐ المفضلة", "quick_review": "⚡ مراجعة سريعة",
        "badges": "🏅 إنجازاتي",
        "welcome": "مرحباً", "subtitle": "منصة 3AC RevisioMaroc لمراجعة شاملة",
        "stats": "📊 إحصائياتك", "points": "النقاط", "level": "المستوى",
        "subjects_count": "المواد", "progress": "التقدم",
        "choose_subject": "اختر مادة للمراجعة", "start_review": "ابدأ المراجعة",
        "tips": "💡 نصيحة: راجع الدروس أولاً، ثم اختبر نفسك!",
        "lessons_bank": "بنك الملخصات والدروس",
        "choose_lesson_subject": "اختر المادة", "quiz_lesson": "📝 اختبار",
        "no_lessons": "⚠️ لا توجد دروس",
        "smart_quizzes": "الاختبارات الذكية", "choose_lesson": "اختر الدرس",
        "start_quiz": "🚀 بدء الاختبار", "questions_count": "عدد الأسئلة",
        "each_correct": "كل إجابة صحيحة = 10 نقاط",
        "final_score": "🎯 نتيجتك النهائية",
        "excellent": "🏆 ممتاز! أداء رائع", "good": "👍 جيد! واصل المجهود",
        "needs_review": "📚 يحتاج إلى مراجعة",
        "correction": "✅ التصحيح", "question": "السؤال", "explanation": "التفسير",
        "retry": "🔄 إعادة", "choose_another": "🔙 درس آخر",
        "submit": "✅ تسليم", "select_answer": "اختر",
        "menu": "📌 القائمة", "your_progress": "🏆 تقدمك",
        "level_progress": "التقدم",
        "theme": "🎨 الثيم", "appearance": "المظهر",
        "language": "🌐 اللغة", "choose_language": "اختر اللغة",
        "congrats": "🎉 مبروك! المستوى",
        "no_questions": "⚠️ لا توجد أسئلة", "back": "🔙 رجوع",
        "quiz_of": "اختبار:", "no_lessons_quiz": "⚠️ لا توجد دروس",
        "student_login": "🎓 دخول التلميذ",
        "developer_login": "⚙️ دخول المطور",
        "register": "📝 إنشاء حساب",
        "guest": "👤 زائر",
        "username": "اسم المستخدم",
        "password": "كلمة المرور", "full_name": "الاسم الكامل",
        "confirm_password": "تأكيد كلمة المرور",
        "login_btn": "دخول", "register_btn": "تسجيل", "logout": "🚪 خروج",
        "auth_subtitle": "اختر طريقة الدخول",
        "wrong_creds": "❌ بيانات خاطئة",
        "guest_note": "💡 كزائر: تصفح بحرية، لكن النتائج لن تُحفظ.",
        "logged_as": "مسجل كـ", "role_student": "تلميذ",
        "role_developer": "مطور", "role_guest": "زائر",
        "student_login_title": "🎓 دخول التلميذ",
        "student_login_subtitle": "أدخل معلوماتك",
        "developer_login_title": "⚙️ دخول المطور",
        "developer_login_subtitle": "للمطور فقط",
        "register_title": "📝 حساب جديد",
        "register_subtitle": "أنشئ حسابك",
        "back_to_login": "🔙 رجوع",
        "register_success": "✅ تم الإنشاء! سجل الدخول",
        "name_required": "⚠️ املأ الحقول",
        "password_mismatch": "❌ كلمتا المرور مختلفتان",
        "developer_panel": "لوحة المطور",
        "add_lesson": "➕ إضافة درس", "add_question": "➕ إضافة سؤال",
        "manage_lessons": "📋 إدارة الدروس", "manage_questions": "❓ إدارة الأسئلة",
        "lesson_title": "العنوان", "lesson_content": "المحتوى",
        "lesson_subject": "المادة", "lesson_language": "اللغة",
        "lesson_image": "📷 صورة", "lesson_pdf": "📄 PDF",
        "save_lesson": "💾 حفظ", "lesson_saved": "✅ تم حفظ الدرس",
        "question_text": "السؤال", "option_a": "A", "option_b": "B",
        "option_c": "C", "option_d": "D",
        "correct_answer": "الإجابة الصحيحة",
        "explanation_text": "التفسير",
        "save_question": "💾 حفظ", "question_saved": "✅ تم حفظ السؤال",
        "select_lesson_for_question": "اختر الدرس",
        "deleted": "✅ تم الحذف",
        "no_custom_lessons": "لا توجد دروس",
        "no_custom_questions": "لا توجد أسئلة",
        "lesson_content_optional": "(اختياري)",
        "lesson_content_label": "محتوى نصي",
        "dev_only_note": "🔒 للمطور Soufiane Ouhazza فقط",
        "owner_public": "📚 دروس المنصة",
        "search_placeholder": "🔍 ابحث عن درس...",
        "add_favorite": "⭐ أضف للمفضلة",
        "remove_favorite": "☆ حذف من المفضلة",
        "my_favorites": "⭐ دروسي المفضلة",
        "no_favorites": "لا توجد دروس فـ المفضلة",
        "my_badges": "🏅 إنجازاتي",
        "no_badges": "لا توجد إنجازات بعد",
        "rank": "اللقب",
        "total_points": "مجموع النقاط",
        "quizzes_taken": "الاختبارات المنجزة",
        "perfect_scores": "العلامات الكاملة",
        "streak": "أيام متتالية",
        "recent_quizzes": "📜 آخر الاختبارات",
        "subject_stats": "📊 إحصائيات المواد",
        "no_history": "لا يوجد سجل بعد",
        "attempts": "المحاولات",
        "avg_score": "المعدل",
        "best_score": "أفضل نتيجة",
        "quick_review_title": "⚡ مراجعة سريعة",
        "quick_review_desc": "10 أسئلة عشوائية من جميع المواد",
        "start_quick": "🚀 ابدأ المراجعة السريعة",
        "daily_bonus": "🎁 مكافأة يومية",
        "time_remaining": "⏱️ الوقت المتبقي",
        "time_up": "⏰ انتهى الوقت!",
    },
}

# باقي الترجمات (fr, en, es) — نستعمل ar كـ fallback
for lang in ["fr", "en", "es"]:
    TRANSLATIONS[lang] = TRANSLATIONS["ar"]

LANGUAGES = {
    "ar": "🇲🇦 العربية",
}

# ----------------------------------------------------------------------------
# الثيمات
# ----------------------------------------------------------------------------
THEMES = {
    "⚽ FC Barcelona": {
        "bg": "#0A1E3F", "card": "#1A2F5C", "text": "#F0F8FF",
        "accent": "#A50044", "secondary": "#0F2A52", "border": "#004D98",
        "highlight": "#00D26A"
    },
    "👑 Real Madrid": {
        "bg": "#0F1B2D", "card": "#1E2E4A", "text": "#FFFFFF",
        "accent": "#FEBE10", "secondary": "#0A1421", "border": "#00529F",
        "highlight": "#FEBE10"
    },
    "🦅 الأهلي": {
        "bg": "#1A0A0A", "card": "#2D1515", "text": "#FFF5F5",
        "accent": "#E30613", "secondary": "#120505", "border": "#8B0000",
        "highlight": "#FFD700"
    },
    "🌙 Moonlight": {
        "bg": "#0A0E1A", "card": "#1A1F35", "text": "#E8ECFF",
        "accent": "#7B9FFF", "secondary": "#050810", "border": "#3D4A7A",
        "highlight": "#FFE57F"
    },
    "🌙 Midnight Purple": {
        "bg": "#0D0B1F", "card": "#1A1735", "text": "#EDE9FE",
        "accent": "#A78BFA", "secondary": "#221D4A", "border": "#3D3475",
        "highlight": "#4ADE80"
    },
    "🌊 Ocean Deep": {
        "bg": "#0A1929", "card": "#132F4C", "text": "#E3F2FD",
        "accent": "#00B8D4", "secondary": "#0F2537", "border": "#1E4976",
        "highlight": "#4ADE80"
    },
    "📚 Study Mode": {
        "bg": "#1A1410", "card": "#2D2418", "text": "#FFF8E7",
        "accent": "#D4A574", "secondary": "#0F0B07", "border": "#5C4A2E",
        "highlight": "#FFD700"
    },
    "🌅 Golden Sunset": {
        "bg": "#1F1410", "card": "#331F17", "text": "#FFF3E0",
        "accent": "#FFB74D", "secondary": "#2A1A12", "border": "#5D3A24",
        "highlight": "#4ADE80"
    },
    "🌿 Forest Emerald": {
        "bg": "#0B1F14", "card": "#143728", "text": "#E8F5E9",
        "accent": "#4ADE80", "secondary": "#0F2A1D", "border": "#1E5C3D",
        "highlight": "#00D26A"
    },
    "☀️ Light Mode": {
        "bg": "#F5F7FA", "card": "#FFFFFF", "text": "#1A202C",
        "accent": "#4A90E2", "secondary": "#E2E8F0", "border": "#CBD5E0",
        "highlight": "#38A169"
    },
}

SUBJECTS = {
    "maths":   {"ar": "الرياضيات",         "icon": "📐", "color": "#4A90E2"},
    "french":  {"ar": "اللغة الفرنسية",     "icon": "🇫🇷", "color": "#E74C3C"},
    "english": {"ar": "اللغة الإنجليزية",   "icon": "🇬🇧", "color": "#3498DB"},
    "history": {"ar": "الاجتماعيات",        "icon": "🌍", "color": "#F39C12"},
    "islamic": {"ar": "التربية الإسلامية",  "icon": "🕌", "color": "#27AE60"},
    "pc":      {"ar": "الفيزياء والكيمياء", "icon": "⚗️", "color": "#9B59B6"},
    "svt":     {"ar": "علوم الحياة والأرض", "icon": "🧬", "color": "#16A085"},
}

def init_session_state():
    defaults = {
        "theme": "⚽ FC Barcelona", "language": "ar", "page": "dashboard",
        "selected_subject": None, "selected_lesson": None,
        "points": 0, "level": 1, "student_name": "",
        "quiz_state": {}, "quiz_finished": False, "current_lesson_title": "",
        "authenticated": False, "user_role": None, "username": None, "full_name": None,
        "auth_page": "home", "quick_review_mode": False,
        "quiz_start_time": None, "quiz_time_limit": 600,
        "daily_bonus_shown": False,
    }
    for k, v in defaults.items():
        if k not in st.session_state:
            st.session_state[k] = v

init_session_state()

def T(key):
    lang = st.session_state.language
    return TRANSLATIONS.get(lang, TRANSLATIONS["ar"]).get(key, key)

def get_subject_name(subject_key):
    return SUBJECTS[subject_key].get("ar", subject_key)

def get_progress_percent():
    stats = get_user_stats(st.session_state.username)
    return stats.get("total_points", 0) % 100 if stats else 0

def apply_theme():
    theme = THEMES[st.session_state.theme]
    direction = "rtl"
    align = "right"
    highlight = theme.get("highlight", "#4ADE80")

    st.markdown(f"""
    <style>
        .stApp {{ background-color: {theme['bg']}; color: {theme['text']}; direction: {direction}; }}
        section[data-testid="stSidebar"] {{ background-color: {theme['secondary']}; border-right: 2px solid {theme['accent']}; }}
        section[data-testid="stSidebar"] * {{ color: {theme['text']} !important; }}
        .custom-card {{
            background-color: {theme['card']}; color: {theme['text']};
            padding: 20px; border-radius: 12px; border: 1px solid {theme['border']};
            margin-bottom: 15px; box-shadow: 0 4px 12px rgba(0,0,0,0.3);
            transition: transform 0.2s; text-align: {align};
        }}
        .custom-card:hover {{ transform: translateY(-3px); border-color: {theme['accent']}; }}
        h1, h2, h3, h4, h5, h6 {{ color: {theme['text']} !important; text-align: {align}; }}
        p, label, div {{ text-align: {align}; }}
        .stButton > button {{
            background: linear-gradient(135deg, {theme['accent']}, {theme['border']});
            color: white; border-radius: 8px;
            border: none; padding: 10px 20px; font-weight: bold;
        }}
        .stButton > button:hover {{ opacity: 0.9; transform: scale(1.02); }}
        .stTextInput input, .stSelectbox select, .stTextArea textarea {{
            background-color: {theme['card']} !important; color: {theme['text']} !important;
            border: 1px solid {theme['border']} !important;
        }}
        .stProgress > div > div > div {{ background: linear-gradient(90deg, {theme['accent']}, {highlight}); }}
        div[data-testid="stMetricValue"] {{ color: {theme['accent']} !important; }}
        .main-header {{
            background: linear-gradient(135deg, {theme['accent']} 0%, {theme['border']} 50%, {theme['accent']} 100%);
            padding: 30px; border-radius: 18px; text-align: center;
            margin-bottom: 25px; box-shadow: 0 8px 25px rgba(0,0,0,0.4);
            border: 2px solid {highlight};
        }}
        .main-header h1, .main-header p {{ color: white !important; text-align: center; text-shadow: 0 2px 8px rgba(0,0,0,0.5); }}
        .main-header h1 {{ margin: 0; font-size: 2.3em; }}
        .role-badge {{
            display: inline-block; padding: 3px 12px; border-radius: 12px;
            font-size: 0.85em; font-weight: bold;
        }}
        .badge-card {{
            background: linear-gradient(135deg, {theme['accent']}, {theme['border']});
            padding: 15px; border-radius: 12px; text-align: center;
            color: white; margin: 5px;
        }}
        .footer {{
            text-align: center; padding: 20px; margin-top: 40px;
            border-top: 2px solid {theme['accent']};
            color: {theme['text']}; opacity: 0.85; font-size: 0.9em;
        }}
        .footer b {{ color: {theme['accent']}; }}
    </style>
    """, unsafe_allow_html=True)
    # ============================================================================
# صفحات المصادقة
# ============================================================================
def render_auth_home():
    apply_theme()

    st.markdown(f"""
    <div class="main-header">
        <h1>🎓 3AC RevisioMaroc</h1>
        <p>{T('auth_subtitle')}</p>
    </div>
    """, unsafe_allow_html=True)

    col1, col2, col3 = st.columns(3)

    with col1:
        st.markdown(f"""
        <div class="custom-card" style="text-align:center; min-height: 180px; border-top: 5px solid #3498DB;">
            <div style="font-size: 3.5em;">🎓</div>
            <h3>{T('student_login')}</h3>
        </div>
        """, unsafe_allow_html=True)
        if st.button(f"🎓 {T('student_login')}", use_container_width=True, key="go_student"):
            st.session_state.auth_page = "student_login"
            st.rerun()

    with col2:
        st.markdown(f"""
        <div class="custom-card" style="text-align:center; min-height: 180px; border-top: 5px solid #E74C3C;">
            <div style="font-size: 3.5em;">⚙️</div>
            <h3>{T('developer_login')}</h3>
        </div>
        """, unsafe_allow_html=True)
        if st.button(f"⚙️ {T('developer_login')}", use_container_width=True, key="go_dev"):
            st.session_state.auth_page = "developer_login"
            st.rerun()

    with col3:
        st.markdown(f"""
        <div class="custom-card" style="text-align:center; min-height: 180px; border-top: 5px solid #27AE60;">
            <div style="font-size: 3.5em;">📝</div>
            <h3>{T('register')}</h3>
        </div>
        """, unsafe_allow_html=True)
        if st.button(f"📝 {T('register')}", use_container_width=True, key="go_register"):
            st.session_state.auth_page = "register"
            st.rerun()

    st.markdown("---")
    col1, col2, col3 = st.columns([1, 2, 1])
    with col2:
        if st.button(f"👤 {T('guest')}", use_container_width=True, key="guest_btn"):
            st.session_state.authenticated = True
            st.session_state.username = "guest"
            st.session_state.user_role = "guest"
            st.session_state.full_name = T('role_guest')
            st.session_state.student_name = T('role_guest')
            st.rerun()
        st.info(T('guest_note'))

    st.markdown(f"""
    <div class="footer">
        © 2026 <b>Soufiane Ouhazza</b> — All Rights Reserved
    </div>
    """, unsafe_allow_html=True)


def render_student_login():
    apply_theme()
    st.markdown(f"""
    <div class="main-header" style="background: linear-gradient(135deg, #3498DB, #004D98);">
        <h1>{T('student_login_title')}</h1>
        <p>{T('student_login_subtitle')}</p>
    </div>
    """, unsafe_allow_html=True)

    col1, col2, col3 = st.columns([1, 2, 1])
    with col2:
        with st.form("student_login_form"):
            username = st.text_input(f"👤 {T('username')}", key="sl_user")
            password = st.text_input(f"🔒 {T('password')}", type="password", key="sl_pass")
            if st.form_submit_button(f"🎓 {T('login_btn')}", use_container_width=True):
                if not username or not password:
                    st.error(T('name_required'))
                else:
                    ok, user = authenticate(username, password)
                    if ok and user["role"] == "student":
                        st.session_state.authenticated = True
                        st.session_state.username = username
                        st.session_state.user_role = "student"
                        st.session_state.full_name = user["full_name"]
                        st.session_state.student_name = user["full_name"]
                        st.session_state.auth_page = "home"
                        st.rerun()
                    elif ok and user["role"] == "developer":
                        st.error("❌ حساب مطور — استخدم صفحة المطور")
                    else:
                        st.error(T('wrong_creds'))

        st.markdown("---")
        c1, c2 = st.columns(2)
        with c1:
            if st.button(f"📝 {T('register')}", use_container_width=True, key="sl_to_reg"):
                st.session_state.auth_page = "register"
                st.rerun()
        with c2:
            if st.button(T('back_to_login'), use_container_width=True, key="sl_back"):
                st.session_state.auth_page = "home"
                st.rerun()


def render_developer_login():
    apply_theme()
    st.markdown(f"""
    <div class="main-header" style="background: linear-gradient(135deg, #A50044, #004D98);">
        <h1>{T('developer_login_title')}</h1>
        <p>{T('developer_login_subtitle')}</p>
    </div>
    """, unsafe_allow_html=True)

    col1, col2, col3 = st.columns([1, 2, 1])
    with col2:
        with st.form("dev_login_form"):
            username = st.text_input(f"👤 {T('username')}", key="dl_user")
            password = st.text_input(f"🔒 {T('password')}", type="password", key="dl_pass")
            if st.form_submit_button(f"⚙️ {T('login_btn')}", use_container_width=True):
                if not username or not password:
                    st.error(T('name_required'))
                else:
                    ok, user = authenticate(username, password)
                    if ok and user["role"] == "developer":
                        st.session_state.authenticated = True
                        st.session_state.username = username
                        st.session_state.user_role = "developer"
                        st.session_state.full_name = user["full_name"]
                        st.session_state.student_name = user["full_name"]
                        st.session_state.auth_page = "home"
                        st.rerun()
                    else:
                        st.error(T('wrong_creds'))

        st.markdown("---")
        if st.button(T('back_to_login'), use_container_width=True, key="dl_back"):
            st.session_state.auth_page = "home"
            st.rerun()


def render_register():
    apply_theme()
    st.markdown(f"""
    <div class="main-header" style="background: linear-gradient(135deg, #27AE60, #004D98);">
        <h1>{T('register_title')}</h1>
        <p>{T('register_subtitle')}</p>
    </div>
    """, unsafe_allow_html=True)

    col1, col2, col3 = st.columns([1, 2, 1])
    with col2:
        with st.form("register_form"):
            new_user = st.text_input(f"👤 {T('username')}", key="rg_user")
            new_name = st.text_input(f"📝 {T('full_name')}", key="rg_name")
            new_pass = st.text_input(f"🔒 {T('password')}", type="password", key="rg_pass")
            confirm_pass = st.text_input(f"🔒 {T('confirm_password')}", type="password", key="rg_pass2")
            if st.form_submit_button(f"📝 {T('register_btn')}", use_container_width=True):
                if not new_user or not new_pass:
                    st.error(T('name_required'))
                elif new_pass != confirm_pass:
                    st.error(T('password_mismatch'))
                else:
                    ok, msg = register_user(new_user, new_pass, new_name)
                    if ok:
                        st.success(T('register_success'))
                    else:
                        st.error(msg)

        st.markdown("---")
        if st.button(T('back_to_login'), use_container_width=True, key="rg_back"):
            st.session_state.auth_page = "home"
            st.rerun()


def render_auth_page():
    p = st.session_state.auth_page
    if p == "home": render_auth_home()
    elif p == "student_login": render_student_login()
    elif p == "developer_login": render_developer_login()
    elif p == "register": render_register()
    else: render_auth_home()

    # ============================================================================
# الرئيسية
# ============================================================================
def render_dashboard():
    username = st.session_state.username
    name = st.session_state.student_name or T('welcome')
    st.markdown(f"""
    <div class="main-header">
        <h1>🎓 {T('welcome')} {name}!</h1>
        <p>{T('subtitle')}</p>
    </div>
    """, unsafe_allow_html=True)

    # المكافأة اليومية
    if st.session_state.user_role == "student" and not st.session_state.get("daily_bonus_shown"):
        bonus = check_daily_bonus(username)
        if bonus > 0:
            st.success(f"🎁 {T('daily_bonus')}: +{bonus} نقطة!")
            st.balloons()
        st.session_state.daily_bonus_shown = True

    # الإحصائيات
    stats = get_user_stats(username)
    total_points = stats.get("total_points", 0)
    level = stats.get("level", 1)
    rank = get_rank(level)

    st.markdown(f"### {T('stats')}")
    c1, c2, c3, c4 = st.columns(4)
    with c1: st.metric(f"🏆 {T('total_points')}", total_points)
    with c2: st.metric(f"⭐ {T('level')}", f"{level} — {rank}")
    with c3: st.metric(f"📝 {T('quizzes_taken')}", stats.get("quizzes_taken", 0))
    with c4: st.metric(f"💯 {T('perfect_scores')}", stats.get("perfect_scores", 0))

    # شريط التقدم
    progress = total_points % 100
    st.progress(progress / 100, text=f"{T('level_progress')}: {progress}/100")

    # ستريك
    streak = stats.get("streak", 0)
    if streak > 0:
        st.info(f"🔥 {T('streak')}: {streak} يوم")

    st.markdown("---")
    st.markdown(f"### 📖 {T('choose_subject')}")

    cols = st.columns(4)
    for idx, (key, info) in enumerate(SUBJECTS.items()):
        with cols[idx % 4]:
            st.markdown(f"""
            <div class="custom-card" style="text-align:center; border-top: 4px solid {info['color']};">
                <div style="font-size: 3em;">{info['icon']}</div>
                <h3 style="margin: 10px 0;">{info['ar']}</h3>
            </div>
            """, unsafe_allow_html=True)
            if st.button(T('start_review'), key=f"subj_{key}", use_container_width=True):
                st.session_state.selected_subject = key
                st.session_state.page = "lessons"
                st.rerun()

    st.markdown("---")
    st.info(T('tips'))

# ============================================================================
# الدروس
# ============================================================================
def render_lessons():
    st.markdown(f"## 📚 {T('lessons_bank')}")

    col1, col2 = st.columns([3, 1])
    with col1:
        search = st.text_input(T('search_placeholder'), key="lesson_search")
    with col2:
        subject_keys = ["all"] + list(SUBJECTS.keys())
        selected_subject = st.selectbox(
            T('choose_lesson_subject'), subject_keys,
            format_func=lambda k: "🎯 كل المواد" if k == "all" else f"{SUBJECTS[k]['icon']} {SUBJECTS[k]['ar']}",
            index=subject_keys.index(st.session_state.selected_subject) if st.session_state.selected_subject in subject_keys else 0
        )

    st.markdown("---")

    subject_filter = None if selected_subject == "all" else selected_subject
    lessons = load_lessons(subject_filter, None, owner="public", search=search or None)

    if not lessons:
        st.warning(T('no_lessons'))
        return

    for lesson in lessons:
        _render_lesson_card(lesson)


def _render_lesson_card(lesson):
    with st.expander(f"📖 {lesson['title']} — *{get_subject_name(lesson['subject'])}*", expanded=False):
        # زر المفضلة
        if st.session_state.user_role == "student":
            is_fav = is_favorite(st.session_state.username, lesson['id'])
            fav_label = T('remove_favorite') if is_fav else T('add_favorite')
            if st.button(fav_label, key=f"fav_{lesson['id']}"):
                toggle_favorite(st.session_state.username, lesson['id'])
                st.rerun()

        if lesson.get('content'):
            st.markdown(lesson['content'])
        if lesson.get('image_url') and os.path.exists(lesson['image_url']):
            st.image(lesson['image_url'], use_container_width=True)
        if lesson.get('pdf_url'):
            st.markdown("#### 📄 PDF")
            render_pdf(lesson['pdf_url'])

        st.markdown("---")
        if st.button(T('quiz_lesson'), key=f"quiz_{lesson['id']}"):
            st.session_state.selected_lesson = lesson['id']
            st.session_state.current_lesson_title = lesson['title']
            st.session_state.page = "quiz"
            st.session_state.quiz_state = {}
            st.session_state.quiz_finished = False
            st.session_state.quick_review_mode = False
            st.session_state.quiz_start_time = time.time()
            st.rerun()

# ============================================================================
# الإحصائيات
# ============================================================================
def render_my_stats():
    username = st.session_state.username
    st.markdown(f"## 📊 {T('my_stats')}")

    stats = get_user_stats(username)
    level = stats.get("level", 1)
    rank = get_rank(level)

    c1, c2, c3, c4 = st.columns(4)
    with c1: st.metric(f"🏆 {T('total_points')}", stats.get("total_points", 0))
    with c2: st.metric(f"⭐ {T('rank')}", rank)
    with c3: st.metric(f"📝 {T('quizzes_taken')}", stats.get("quizzes_taken", 0))
    with c4: st.metric(f"🔥 {T('streak')}", f"{stats.get('streak', 0)} يوم")

    st.markdown("---")

    # إحصائيات المواد
    st.markdown(f"### {T('subject_stats')}")
    subject_stats = get_subject_stats(username)
    if subject_stats:
        for s in subject_stats:
            subj_name = get_subject_name(s['subject']) if s['subject'] in SUBJECTS else s['subject']
            icon = SUBJECTS.get(s['subject'], {}).get('icon', '📚')
            with st.expander(f"{icon} {subj_name}"):
                c1, c2, c3 = st.columns(3)
                with c1: st.metric(T('attempts'), s['attempts'])
                with c2: st.metric(T('avg_score'), f"{s['avg_percent']:.1f}%")
                with c3: st.metric(T('best_score'), f"{s['best_percent']:.0f}%")
    else:
        st.info(T('no_history'))

    st.markdown("---")

    # آخر الاختبارات
    st.markdown(f"### {T('recent_quizzes')}")
    history = get_quiz_history(username, limit=10)
    if history:
        for h in history:
            icon = "🏆" if h['percent'] >= 80 else "👍" if h['percent'] >= 50 else "📚"
            st.markdown(f"{icon} **{h['lesson_title']}** — {h['score']}/{h['total']} ({h['percent']:.0f}%) — *{h['created_at'][:16]}*")
    else:
        st.info(T('no_history'))

    # الإنجازات
    st.markdown("---")
    st.markdown(f"### {T('my_badges')}")
    badges = get_user_badges(username)
    if badges:
        cols = st.columns(4)
        for idx, b in enumerate(badges):
            with cols[idx % 4]:
                st.markdown(f"""
                <div class="badge-card">
                    <div style="font-size: 2.5em;">{b['icon']}</div>
                    <h4>{b['name']}</h4>
                    <p style="font-size: 0.85em; opacity: 0.9;">{b['desc']}</p>
                </div>
                """, unsafe_allow_html=True)
    else:
        st.info(T('no_badges'))

# ============================================================================
# المفضلة
# ============================================================================
def render_favorites():
    st.markdown(f"## {T('my_favorites')}")
    favs = get_favorites(st.session_state.username)
    if not favs:
        st.info(T('no_favorites'))
        return
    for lesson in favs:
        _render_lesson_card(lesson)

# ============================================================================
# المراجعة السريعة
# ============================================================================
def render_quick_review():
    st.markdown(f"## {T('quick_review_title')}")
    st.caption(T('quick_review_desc'))

    if not st.session_state.quick_review_mode:
        all_lessons = load_lessons(owner="public")
        all_questions = []
        for l in all_lessons:
            qs = load_questions(l['id'])
            for q in qs:
                q['lesson_title'] = l['title']
                q['subject'] = l['subject']
                all_questions.append(q)

        if len(all_questions) < 1:
            st.warning("⚠️ ما كايناش أسئلة كافية")
            return

        st.info(f"📊 متوفر: {len(all_questions)} سؤال")
        if st.button(T('start_quick'), use_container_width=True):
            sample = random.sample(all_questions, min(10, len(all_questions)))
            st.session_state.quick_review_mode = True
            st.session_state.quiz_state = {"questions": sample, "answers": {}, "score": 0}
            st.session_state.quiz_finished = False
            st.session_state.selected_lesson = "quick"
            st.session_state.current_lesson_title = "⚡ مراجعة سريعة"
            st.session_state.quiz_start_time = time.time()
            st.rerun()
        return

    questions = st.session_state.quiz_state.get("questions", [])
    if not questions:
        st.session_state.quick_review_mode = False
        st.rerun()

    _render_quiz_ui(questions, "quick")# ============================================================================
# واجهة الاختبار (مشتركة)
# ============================================================================
def _render_quiz_ui(questions, lesson_id):
    username = st.session_state.username

    # المؤقت
    if st.session_state.quiz_start_time and not st.session_state.quiz_finished:
        elapsed = time.time() - st.session_state.quiz_start_time
        remaining = st.session_state.quiz_time_limit - elapsed

        if remaining > 0:
            mins = int(remaining // 60)
            secs = int(remaining % 60)
            st.warning(f"⏱️ {T('time_remaining')}: {mins:02d}:{secs:02d}")
        else:
            st.error(T('time_up'))
            st.session_state.quiz_finished = True

    st.markdown(f"""
    <div class="custom-card">
        <h3>📝 {st.session_state.get('current_lesson_title', '')}</h3>
        <p>{T('questions_count')}: {len(questions)} | {T('each_correct')}</p>
    </div>
    """, unsafe_allow_html=True)

    if st.session_state.quiz_finished:
        score = st.session_state.quiz_state.get('score', 0)
        total = len(questions)
        percent = (score / total) * 100 if total > 0 else 0
        msg = T('excellent') if percent >= 80 else T('good') if percent >= 50 else T('needs_review')

        st.markdown(f"""
        <div class="custom-card" style="text-align:center; border: 2px solid {THEMES[st.session_state.theme]['accent']};">
            <h2>{T('final_score')}</h2>
            <h1 style="font-size: 3em; color: {THEMES[st.session_state.theme]['accent']};">{score} / {total}</h1>
            <h3>{percent:.0f}%</h3>
            <p>{msg}</p>
        </div>
        """, unsafe_allow_html=True)

        if percent >= 80:
            st.balloons()

        st.markdown(f"### {T('correction')}")
        answers = st.session_state.quiz_state.get('answers', {})
        for i, q in enumerate(questions):
            user_answer = answers.get(i)
            is_correct = user_answer == q['correct']
            icon = "✅" if is_correct else "❌"
            with st.expander(f"{icon} {T('question')} {i+1}: {q['question']}"):
                for j, opt in enumerate(q['options']):
                    marker = "🟢" if j == q['correct'] else ("🔴" if j == user_answer else "⚪")
                    st.markdown(f"{marker} {chr(65+j)}. {opt}")
                if q.get('explanation'):
                    st.info(f"💡 **{T('explanation')}:** {q['explanation']}")

        c1, c2 = st.columns(2)
        with c1:
            if st.button(T('retry'), use_container_width=True):
                st.session_state.quiz_state = {'answers': {}}
                st.session_state.quiz_finished = False
                st.session_state.quiz_start_time = time.time()
                st.rerun()
        with c2:
            if st.button(T('choose_another'), use_container_width=True):
                st.session_state.selected_lesson = None
                st.session_state.quiz_finished = False
                st.session_state.quick_review_mode = False
                st.session_state.quiz_state = {}
                st.rerun()
        return

    answers = st.session_state.quiz_state.get('answers', {})

    with st.form("quiz_form"):
        for i, q in enumerate(questions):
            st.markdown(f"**{T('question')} {i+1}:** {q['question']}")
            options = q['options']
            choice = st.radio(
                T('select_answer'), options=range(len(options)),
                format_func=lambda j, opts=options: f"{chr(65+j)}. {opts[j]}",
                key=f"q_{i}", index=answers.get(i, 0),
                label_visibility="collapsed"
            )
            answers[i] = choice
            st.markdown("---")

        if st.form_submit_button(T('submit'), use_container_width=True):
            score = sum(1 for i, q in enumerate(questions) if answers.get(i) == q['correct'])
            st.session_state.quiz_state = {'answers': answers, 'score': score}
            st.session_state.quiz_finished = True

            if st.session_state.user_role == "student":
                subject = questions[0].get('subject', 'mixed') if questions else 'mixed'
                save_quiz_result(username, lesson_id,
                                st.session_state.current_lesson_title,
                                subject, score, len(questions))
                update_user_stats(username, points=score * 10, quiz_taken=True,
                                perfect=(score == len(questions)), subject=subject)
            st.rerun()


# ============================================================================
# الاختبارات
# ============================================================================
def render_quiz():
    st.markdown(f"## 📝 {T('smart_quizzes')}")

    if not st.session_state.selected_lesson:
        all_lessons = load_lessons(owner="public")
        if not all_lessons:
            st.warning(T('no_lessons_quiz'))
            return

        lesson_titles = {str(l['id']): f"{l['title']} ({get_subject_name(l['subject'])})" for l in all_lessons}
        lesson_id = st.selectbox(T('choose_lesson'), list(lesson_titles.keys()),
                                  format_func=lambda i: lesson_titles[i])

        if st.button(T('start_quiz')):
            st.session_state.selected_lesson = lesson_id
            st.session_state.current_lesson_title = lesson_titles[lesson_id]
            st.session_state.quiz_state = {}
            st.session_state.quiz_finished = False
            st.session_state.quick_review_mode = False
            st.session_state.quiz_start_time = time.time()
            st.rerun()
        return

    if st.session_state.quick_review_mode:
        render_quick_review()
        return

    lesson_id = st.session_state.selected_lesson
    questions = load_questions(lesson_id)

    if not questions:
        st.warning(T('no_questions'))
        if st.button(T('back')):
            st.session_state.selected_lesson = None
            st.rerun()
        return

    _render_quiz_ui(questions, lesson_id)


# ============================================================================
# لوحة المطور
# ============================================================================
def render_developer_panel():
    if st.session_state.user_role != "developer":
        st.error("🔒 للمطور فقط")
        st.stop()

    st.markdown(f"## ⚙️ {T('developer_panel')}")

    # إحصائيات عامة
    conn = get_db()
    c = conn.cursor()
    c.execute("SELECT COUNT(*) FROM users WHERE role='student'")
    total_students = c.fetchone()[0]
    c.execute("SELECT COUNT(*) FROM lessons WHERE owner='public'")
    total_lessons = c.fetchone()[0]
    c.execute("SELECT COUNT(*) FROM questions")
    total_questions = c.fetchone()[0]
    c.execute("SELECT COUNT(*) FROM quiz_history")
    total_attempts = c.fetchone()[0]
    conn.close()

    c1, c2, c3, c4 = st.columns(4)
    with c1: st.metric("👥 التلاميذ", total_students)
    with c2: st.metric("📚 الدروس", total_lessons)
    with c3: st.metric("❓ الأسئلة", total_questions)
    with c4: st.metric("📝 المحاولات", total_attempts)

    st.markdown("---")
    tab1, tab2 = st.tabs([T('manage_lessons'), T('manage_questions')])

    with tab1:
        st.markdown(f"### {T('add_lesson')}")
        with st.form("add_lesson_form", clear_on_submit=True):
            c1, c2 = st.columns(2)
            with c1:
                subject = st.selectbox(T('lesson_subject'), list(SUBJECTS.keys()),
                                       format_func=lambda k: f"{SUBJECTS[k]['icon']} {SUBJECTS[k]['ar']}")
            with c2:
                language = st.selectbox(T('lesson_language'), list(LANGUAGES.keys()),
                                        format_func=lambda k: LANGUAGES[k])
            title = st.text_input(T('lesson_title'))
            content = st.text_area(T('lesson_content_label'), height=150)
            c1, c2 = st.columns(2)
            with c1: image_file = st.file_uploader(T('lesson_image'), type=["png", "jpg", "jpeg", "webp"])
            with c2: pdf_file = st.file_uploader(T('lesson_pdf'), type=["pdf"])

            if st.form_submit_button(T('save_lesson'), use_container_width=True):
                if title and (content or image_file or pdf_file):
                    image_url = upload_file(image_file, "developer/images") if image_file else None
                    pdf_url = upload_file(pdf_file, "developer/pdfs") if pdf_file else None
                    ok, msg = add_lesson(subject, language, title, content or "", image_url, pdf_url, owner="public")
                    if ok:
                        st.success(T('lesson_saved'))
                        st.rerun()
                    else:
                        st.error(msg)
                else:
                    st.error("⚠️ املأ العنوان + (نص أو صورة أو PDF)")

        st.markdown("---")
        st.markdown(f"### {T('manage_lessons')}")
        all_lessons = load_lessons(owner="public")
        if all_lessons:
            for lesson in all_lessons:
                c1, c2 = st.columns([5, 1])
                with c1:
                    icons = ""
                    if lesson.get('content'): icons += "📝"
                    if lesson.get('image_url'): icons += "📷"
                    if lesson.get('pdf_url'): icons += "📄"
                    st.markdown(f"{icons} **{lesson['title']}** — {get_subject_name(lesson['subject'])}")
                with c2:
                    if st.button("🗑️", key=f"del_{lesson['id']}"):
                        if delete_lesson(lesson['id'], owner_filter="public"):
                            st.success(T('deleted'))
                            st.rerun()
        else:
            st.info(T('no_custom_lessons'))

    with tab2:
        st.markdown(f"### {T('add_question')}")
        all_lessons = load_lessons(owner="public")
        lesson_options = {str(l['id']): f"[{get_subject_name(l['subject'])}] {l['title']}" for l in all_lessons}

        if not lesson_options:
            st.warning("⚠️ أضف درساً أولاً")
        else:
            with st.form("add_question_form", clear_on_submit=True):
                lesson_id = st.selectbox(T('select_lesson_for_question'),
                                          list(lesson_options.keys()),
                                          format_func=lambda i: lesson_options[i])
                q_text = st.text_area(T('question_text'))
                c1, c2 = st.columns(2)
                with c1:
                    opt_a = st.text_input(T('option_a'))
                    opt_b = st.text_input(T('option_b'))
                with c2:
                    opt_c = st.text_input(T('option_c'))
                    opt_d = st.text_input(T('option_d'))
                correct = st.radio(T('correct_answer'), options=[0, 1, 2, 3],
                                    format_func=lambda i: f"{chr(65+i)}", horizontal=True)
                explanation = st.text_input(T('explanation_text'))

                if st.form_submit_button(T('save_question'), use_container_width=True):
                    if q_text and opt_a and opt_b and opt_c and opt_d:
                        correct_letter = chr(65 + correct)
                        ok, msg = add_question(lesson_id, q_text, opt_a, opt_b, opt_c, opt_d, correct_letter, explanation)
                        if ok:
                            st.success(T('question_saved'))
                            st.rerun()
                        else:
                            st.error(msg)
                    else:
                        st.error("⚠️ املأ الحقول")

        st.markdown("---")
        st.markdown(f"### {T('manage_questions')}")
        for l in all_lessons:
            qs = load_questions(l['id'])
            if qs:
                st.markdown(f"**📖 {l['title']}**")
                for q in qs:
                    c1, c2 = st.columns([5, 1])
                    with c1:
                        st.markdown(f"❓ {q['question']} — ✅ **{chr(65+q['correct'])}**")
                    with c2:
                        if st.button("🗑️", key=f"delq_{q['id']}"):
                            delete_question(q['id'])
                            st.rerun()


# ============================================================================
# التوجيه الرئيسي
# ============================================================================
if not st.session_state.authenticated:
    render_auth_page()
    st.stop()

apply_theme()
theme_colors = THEMES[st.session_state.theme]

with st.sidebar:
    st.markdown(f"""
    <div style="text-align:center; padding: 15px 0;">
        <h1 style="color:{theme_colors['accent']}; margin:0;">🎓 3AC</h1>
        <h2 style="margin:5px 0;">RevisioMaroc</h2>
    </div>
    """, unsafe_allow_html=True)

    role = st.session_state.user_role
    role_label = {"student": T('role_student'), "developer": T('role_developer'),
                  "guest": T('role_guest')}.get(role, role)
    badge_color = {"student": "#3498DB", "developer": theme_colors['accent'], "guest": "#95A5A6"}.get(role, "#4A90E2")

    st.markdown(f"""
    <div class="custom-card" style="text-align:center; padding: 12px;">
        <p style="margin:0; font-size: 0.9em; opacity: 0.7;">{T('logged_as')}</p>
        <p style="margin:5px 0; font-weight: bold;">{st.session_state.full_name or st.session_state.username}</p>
        <span class="role-badge" style="background:{badge_color}; color:white;">{role_label}</span>
    </div>
    """, unsafe_allow_html=True)

    if role == "student":
        stats = get_user_stats(st.session_state.username)
        level = stats.get("level", 1)
        rank = get_rank(level)
        st.markdown(f"""
        <div class="custom-card" style="text-align:center; padding: 12px;">
            <p style="margin:0; font-size: 1.1em;">{rank}</p>
            <p style="margin:5px 0; opacity: 0.8;">🏆 {stats.get('total_points', 0)} نقطة</p>
        </div>
        """, unsafe_allow_html=True)

    st.markdown("---")

    st.markdown(f"### {T('theme')}")
    theme_keys = list(THEMES.keys())
    selected_theme = st.selectbox(T('appearance'), theme_keys,
                                   index=theme_keys.index(st.session_state.theme),
                                   label_visibility="collapsed")
    if selected_theme != st.session_state.theme:
        st.session_state.theme = selected_theme
        st.rerun()

    st.markdown("---")
    st.markdown(f"### {T('menu')}")

    if st.button(T('dashboard'), use_container_width=True):
        st.session_state.page = "dashboard"
        st.session_state.selected_subject = None
        st.session_state.selected_lesson = None
        st.session_state.quick_review_mode = False
        st.rerun()
    if st.button(T('lessons'), use_container_width=True):
        st.session_state.page = "lessons"
        st.rerun()
    if st.button(T('quizzes'), use_container_width=True):
        st.session_state.page = "quiz"
        st.session_state.selected_lesson = None
        st.session_state.quick_review_mode = False
        st.rerun()
    if st.button(T('quick_review'), use_container_width=True):
        st.session_state.page = "quick_review"
        st.session_state.quick_review_mode = False
        st.session_state.selected_lesson = None
        st.rerun()

    if role == "student":
        if st.button(T('favorites'), use_container_width=True):
            st.session_state.page = "favorites"
            st.rerun()
        if st.button(T('my_stats'), use_container_width=True):
            st.session_state.page = "my_stats"
            st.rerun()

    if role == "developer":
        if st.button(T('developer'), use_container_width=True):
            st.session_state.page = "developer"
            st.rerun()

    st.markdown("---")

    if st.button(T('logout'), use_container_width=True):
        for key in list(st.session_state.keys()):
            del st.session_state[key]
        st.rerun()

    st.markdown(f"""
    <div style="text-align:center; padding: 15px; opacity: 0.75; font-size: 0.85em;">
        © 2026 <b>Soufiane Ouhazza</b><br>All Rights Reserved
    </div>
    """, unsafe_allow_html=True)

page = st.session_state.page

if page == "developer" and st.session_state.user_role != "developer":
    st.error("🔒 محمية")
    st.session_state.page = "dashboard"
    st.rerun()

if page == "dashboard": render_dashboard()
elif page == "lessons": render_lessons()
elif page == "quiz": render_quiz()
elif page == "quick_review": render_quick_review()
elif page == "favorites" and st.session_state.user_role == "student": render_favorites()
elif page == "my_stats" and st.session_state.user_role == "student": render_my_stats()
elif page == "developer" and st.session_state.user_role == "developer": render_developer_panel()
else: render_dashboard()

st.markdown(f"""
<div class="footer">
    © 2026 <b>Soufiane Ouhazza</b> — 3AC RevisioMaroc
</div>
""", unsafe_allow_html=True)
    
