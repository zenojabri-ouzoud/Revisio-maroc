import streamlit as st
import hashlib
import sqlite3
import os
import base64
import random
import time
import json
import datetime
from pathlib import Path

# ============================================================
# 3AC RevisioMaroc — Application éducative complète
# ============================================================

APP_NAME = "3AC RevisioMaroc"
DB_PATH = "revisiomaroc.db"
UPLOAD_DIR = "uploads"
os.makedirs(UPLOAD_DIR, exist_ok=True)

st.set_page_config(
    page_title=APP_NAME,
    page_icon="📚",
    layout="wide",
    initial_sidebar_state="expanded",
)

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
    "⚽ FC Barcelona": {
        "bg": "#0A1E3F", "card": "#1A2F5C", "text": "#F0F8FF",
        "accent": "#A50044", "secondary": "#0F2A52",
        "border": "#004D98", "highlight": "#00D26A",
    },
    "👑 Real Madrid": {
        "bg": "#0F1B2D", "card": "#1E2E4A", "text": "#FFFFFF",
        "accent": "#FEBE10", "secondary": "#0A1421",
        "border": "#00529F", "highlight": "#FEBE10",
    },
    "🦅 الأهلي": {
        "bg": "#1A0A0A", "card": "#2D1515", "text": "#FFF5F5",
        "accent": "#E30613", "secondary": "#120505",
        "border": "#8B0000", "highlight": "#FFD700",
    },
    "🌙 Moonlight": {
        "bg": "#0A0E1A", "card": "#1A1F35", "text": "#E8ECFF",
        "accent": "#7B9FFF", "secondary": "#050810",
        "border": "#3D4A7A", "highlight": "#FFE57F",
    },
    "🌙 Midnight Purple": {
        "bg": "#0D0B1F", "card": "#1A1735", "text": "#EDE9FE",
        "accent": "#A78BFA", "secondary": "#221D4A",
        "border": "#3D3475", "highlight": "#4ADE80",
    },
    "🌊 Ocean Deep": {
        "bg": "#0A1929", "card": "#132F4C", "text": "#E3F2FD",
        "accent": "#00B8D4", "secondary": "#0F2537",
        "border": "#1E4976", "highlight": "#4ADE80",
    },
    "📚 Study Mode": {
        "bg": "#1A1410", "card": "#2D2418", "text": "#FFF8E7",
        "accent": "#D4A574", "secondary": "#0F0B07",
        "border": "#5C4A2E", "highlight": "#FFD700",
    },
    "🌅 Golden Sunset": {
        "bg": "#1F1410", "card": "#331F17", "text": "#FFF3E0",
        "accent": "#FFB74D", "secondary": "#2A1A12",
        "border": "#5D3A24", "highlight": "#4ADE80",
    },
    "🌿 Forest Emerald": {
        "bg": "#0B1F14", "card": "#143728", "text": "#E8F5E9",
        "accent": "#4ADE80", "secondary": "#0F2A1D",
        "border": "#1E5C3D", "highlight": "#00D26A",
    },
    "☀️ Light Mode": {
        "bg": "#F5F7FA", "card": "#FFFFFF", "text": "#1A202C",
        "accent": "#4A90E2", "secondary": "#E2E8F0",
        "border": "#CBD5E0", "highlight": "#38A169",
    },
    "🌌 Galaxy": {
        "bg": "#0D0221", "card": "#1A0533", "text": "#E8D5FF",
        "accent": "#C77DFF", "secondary": "#050011",
        "border": "#7209B7", "highlight": "#4CC9F0",
    },
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

TRANSLATIONS = {
    "ar": {
        "home": "الرئيسية", "lessons": "الدروس", "quiz": "الاختبارات",
        "review": "مراجعة سريعة", "flashcards": "بطاقات الحفظ",
        "plan": "خطة المراجعة", "friends": "الأصدقاء",
        "leaderboard": "لوحة المتصدرين", "report": "التقرير الأسبوعي",
        "notifications": "الإشعارات", "stats": "إحصائياتي",
        "favorites": "المفضلة", "developer": "لوحة المطور",
        "logout": "تسجيل الخروج", "language": "اللغة",
        "theme": "الثيم", "profile": "الملف الشخصي",
    },
    "fr": {
        "home": "Accueil", "lessons": "Leçons", "quiz": "Quiz",
        "review": "Révision rapide", "flashcards": "Flashcards",
        "plan": "Plan d'étude", "friends": "Amis",
        "leaderboard": "Classement", "report": "Rapport hebdomadaire",
        "notifications": "Notifications", "stats": "Mes statistiques",
        "favorites": "Favoris", "developer": "Panneau développeur",
        "logout": "Déconnexion", "language": "Langue",
        "theme": "Thème", "profile": "Profil",
    },
    "en": {
        "home": "Home", "lessons": "Lessons", "quiz": "Quizzes",
        "review": "Quick review", "flashcards": "Flashcards",
        "plan": "Study plan", "friends": "Friends",
        "leaderboard": "Leaderboard", "report": "Weekly report",
        "notifications": "Notifications", "stats": "My statistics",
        "favorites": "Favorites", "developer": "Developer panel",
        "logout": "Log out", "language": "Language",
        "theme": "Theme", "profile": "Profile",
    },
}


# ============================================================
# DATABASE
# ============================================================

def get_db():
    conn = sqlite3.connect(DB_PATH, timeout=15)
    conn.row_factory = sqlite3.Row
    conn.execute("PRAGMA foreign_keys = ON")
    return conn


def hash_password(p):
    return hashlib.sha256(p.encode("utf-8")).hexdigest()


def init_db():
    with get_db() as conn:
        conn.executescript("""
        CREATE TABLE IF NOT EXISTS users (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            username TEXT UNIQUE NOT NULL,
            password_hash TEXT NOT NULL,
            role TEXT NOT NULL DEFAULT 'student',
            full_name TEXT NOT NULL DEFAULT '',
            created_at TEXT NOT NULL
        );

        CREATE TABLE IF NOT EXISTS lessons (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            subject TEXT NOT NULL,
            language TEXT NOT NULL DEFAULT 'ar',
            title TEXT NOT NULL,
            content TEXT NOT NULL,
            image_url TEXT DEFAULT '',
            pdf_url TEXT DEFAULT '',
            owner TEXT NOT NULL,
            created_at TEXT NOT NULL
        );

        CREATE TABLE IF NOT EXISTS questions (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            lesson_id INTEGER NOT NULL,
            question TEXT NOT NULL,
            option_a TEXT NOT NULL,
            option_b TEXT NOT NULL,
            option_c TEXT NOT NULL DEFAULT '',
            option_d TEXT NOT NULL DEFAULT '',
            correct_answer TEXT NOT NULL,
            explanation TEXT DEFAULT '',
            FOREIGN KEY (lesson_id) REFERENCES lessons(id) ON DELETE CASCADE
        );

        CREATE TABLE IF NOT EXISTS quiz_history (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            username TEXT NOT NULL,
            lesson_id INTEGER,
            lesson_title TEXT NOT NULL DEFAULT '',
            subject TEXT NOT NULL DEFAULT '',
            score INTEGER NOT NULL,
            total INTEGER NOT NULL,
            percent REAL NOT NULL,
            created_at TEXT NOT NULL
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
            total_points INTEGER NOT NULL DEFAULT 0,
            level INTEGER NOT NULL DEFAULT 1,
            quizzes_taken INTEGER NOT NULL DEFAULT 0,
            perfect_scores INTEGER NOT NULL DEFAULT 0,
            unique_subjects TEXT NOT NULL DEFAULT '[]',
            badges TEXT NOT NULL DEFAULT '[]',
            last_daily TEXT NOT NULL DEFAULT '',
            streak INTEGER NOT NULL DEFAULT 0
        );

        CREATE TABLE IF NOT EXISTS reviews (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            lesson_id INTEGER NOT NULL,
            username TEXT NOT NULL,
            rating INTEGER NOT NULL CHECK(rating BETWEEN 1 AND 5),
            comment TEXT DEFAULT '',
            UNIQUE(lesson_id, username),
            FOREIGN KEY (lesson_id) REFERENCES lessons(id) ON DELETE CASCADE
        );

        CREATE TABLE IF NOT EXISTS messages (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            lesson_id INTEGER NOT NULL,
            username TEXT NOT NULL,
            message TEXT NOT NULL,
            created_at TEXT NOT NULL DEFAULT '',
            FOREIGN KEY (lesson_id) REFERENCES lessons(id) ON DELETE CASCADE
        );

        CREATE TABLE IF NOT EXISTS notifications (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            username TEXT NOT NULL,
            title TEXT NOT NULL,
            message TEXT NOT NULL,
            icon TEXT NOT NULL DEFAULT '🔔',
            is_read INTEGER NOT NULL DEFAULT 0
        );

        CREATE TABLE IF NOT EXISTS flashcards (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            username TEXT NOT NULL,
            subject TEXT NOT NULL,
            front TEXT NOT NULL,
            back TEXT NOT NULL,
            known INTEGER NOT NULL DEFAULT 0
        );

        CREATE TABLE IF NOT EXISTS notes (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            username TEXT NOT NULL,
            lesson_id INTEGER NOT NULL,
            note TEXT NOT NULL,
            created_at TEXT NOT NULL DEFAULT '',
            FOREIGN KEY (lesson_id) REFERENCES lessons(id) ON DELETE CASCADE
        );

        CREATE TABLE IF NOT EXISTS friends (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            username TEXT NOT NULL,
            friend_username TEXT NOT NULL,
            status TEXT NOT NULL DEFAULT 'pending',
            UNIQUE(username, friend_username)
        );

        CREATE TABLE IF NOT EXISTS study_plan (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            username TEXT NOT NULL,
            subject TEXT NOT NULL,
            priority TEXT NOT NULL DEFAULT 'normal',
            target_date TEXT NOT NULL,
            completed INTEGER NOT NULL DEFAULT 0
        );
        """)

        # Developer account: created automatically if absent.
        conn.execute("""
            INSERT OR IGNORE INTO users
            (username, password_hash, role, full_name, created_at)
            VALUES (?, ?, 'developer', ?, ?)
        """, (
            "soufianeDEV",
            hash_password("soufiane2030"),
            "Soufiane Ouhazza",
            datetime.datetime.now().isoformat(timespec="seconds"),
        ))

        conn.execute("""
            INSERT OR IGNORE INTO user_stats (username) VALUES (?)
        """, ("soufianeDEV",))


def register_user(u, p, n):
    u = u.strip()
    n = n.strip()
    if len(u) < 3 or len(p) < 6 or not n:
        return False, "اسم المستخدم يجب أن يتكون من 3 أحرف على الأقل، وكلمة المرور من 6 أحرف."
    try:
        with get_db() as conn:
            conn.execute("""
                INSERT INTO users(username, password_hash, role, full_name, created_at)
                VALUES (?, ?, 'student', ?, ?)
            """, (
                u, hash_password(p), n,
                datetime.datetime.now().isoformat(timespec="seconds"),
            ))
            conn.execute("INSERT INTO user_stats(username) VALUES (?)", (u,))
        return True, "تم إنشاء الحساب بنجاح."
    except sqlite3.IntegrityError:
        return False, "اسم المستخدم مستعمل بالفعل."


def authenticate(u, p):
    with get_db() as conn:
        row = conn.execute("""
            SELECT username, password_hash, role, full_name
            FROM users WHERE username = ?
        """, (u.strip(),)).fetchone()
    if row and row["password_hash"] == hash_password(p):
        return dict(row)
    return None


def get_user_stats(u):
    with get_db() as conn:
        row = conn.execute(
            "SELECT * FROM user_stats WHERE username = ?", (u,)
        ).fetchone()
        if row:
            return dict(row)
        conn.execute("INSERT OR IGNORE INTO user_stats(username) VALUES (?)", (u,))
        row = conn.execute(
            "SELECT * FROM user_stats WHERE username = ?", (u,)
        ).fetchone()
        return dict(row)


def update_user_stats(u, points, quiz, perfect, subject):
    with get_db() as conn:
        conn.execute("INSERT OR IGNORE INTO user_stats(username) VALUES (?)", (u,))
        row = conn.execute(
            "SELECT * FROM user_stats WHERE username = ?", (u,)
        ).fetchone()

        subjects = json.loads(row["unique_subjects"] or "[]")
        if subject and subject not in subjects:
            subjects.append(subject)

        total_points = int(row["total_points"]) + int(points)
        quizzes = int(row["quizzes_taken"]) + (1 if quiz else 0)
        perfect_scores = int(row["perfect_scores"]) + (1 if perfect else 0)
        level = total_points // 100 + 1

        conn.execute("""
            UPDATE user_stats
            SET total_points=?, level=?, quizzes_taken=?, perfect_scores=?,
                unique_subjects=?
            WHERE username=?
        """, (
            total_points, level, quizzes, perfect_scores,
            json.dumps(subjects, ensure_ascii=False), u,
        ))

    check_badges(u)


def save_quiz_result(username, lesson_id, lesson_title, subject, score, total):
    percent = round((score / total) * 100, 2) if total else 0
    with get_db() as conn:
        conn.execute("""
            INSERT INTO quiz_history
            (username, lesson_id, lesson_title, subject, score, total, percent, created_at)
            VALUES (?, ?, ?, ?, ?, ?, ?, ?)
        """, (
            username, lesson_id, lesson_title, subject, score, total,
            percent, datetime.datetime.now().isoformat(timespec="seconds"),
        ))
    update_user_stats(
        username, score * 10, True, bool(total and score == total), subject
    )
    if total and score == total:
        add_notification(username, "علامة كاملة!", "أجبت عن جميع الأسئلة بشكل صحيح.", "💯")
    return percent


def get_quiz_history(u, limit=20):
    with get_db() as conn:
        rows = conn.execute("""
            SELECT * FROM quiz_history WHERE username=?
            ORDER BY id DESC LIMIT ?
        """, (u, int(limit))).fetchall()
    return [dict(r) for r in rows]


def get_subject_stats(u):
    with get_db() as conn:
        rows = conn.execute("""
            SELECT subject, COUNT(*) AS quizzes, AVG(percent) AS average,
                   MAX(percent) AS best
            FROM quiz_history WHERE username=?
            GROUP BY subject ORDER BY average ASC
        """, (u,)).fetchall()
    return [dict(r) for r in rows]


def get_weaknesses(u):
    return [r for r in get_subject_stats(u) if r["average"] is not None and r["average"] < 70]


def get_leaderboard(period="all"):
    with get_db() as conn:
        if period == "week":
            cutoff = (datetime.datetime.now() - datetime.timedelta(days=7)).isoformat()
            rows = conn.execute("""
                SELECT username, SUM(score*10) AS points, COUNT(*) AS quizzes,
                       AVG(percent) AS average
                FROM quiz_history WHERE created_at >= ?
                GROUP BY username ORDER BY points DESC LIMIT 50
            """, (cutoff,)).fetchall()
        elif period == "month":
            cutoff = (datetime.datetime.now() - datetime.timedelta(days=30)).isoformat()
            rows = conn.execute("""
                SELECT username, SUM(score*10) AS points, COUNT(*) AS quizzes,
                       AVG(percent) AS average
                FROM quiz_history WHERE created_at >= ?
                GROUP BY username ORDER BY points DESC LIMIT 50
            """, (cutoff,)).fetchall()
        else:
            rows = conn.execute("""
                SELECT username, total_points AS points,
                       quizzes_taken AS quizzes, total_points AS average
                FROM user_stats ORDER BY total_points DESC LIMIT 50
            """).fetchall()
    return [dict(r) for r in rows]


def get_weekly_report(u):
    cutoff = (datetime.datetime.now() - datetime.timedelta(days=7)).isoformat()
    with get_db() as conn:
        rows = conn.execute("""
            SELECT COUNT(*) AS quizzes, COALESCE(SUM(score),0) AS correct,
                   COALESCE(SUM(total),0) AS questions,
                   COALESCE(AVG(percent),0) AS average
            FROM quiz_history WHERE username=? AND created_at>=?
        """, (u, cutoff)).fetchone()
    return dict(rows)


def check_badges(u):
    stats = get_user_stats(u)
    quizzes = stats["quizzes_taken"]
    level = stats["level"]
    streak = stats["streak"]
    subjects = json.loads(stats["unique_subjects"] or "[]")
    earned = set(json.loads(stats["badges"] or "[]"))

    if quizzes >= 1:
        earned.add("first_quiz")
    if stats["perfect_scores"] >= 1:
        earned.add("perfect")
    for threshold in (5, 10, 25, 50, 100):
        if quizzes >= threshold:
            earned.add(f"{threshold}_quizzes")
    for threshold in (5, 10, 20, 50):
        if level >= threshold:
            earned.add(f"level_{threshold}")
    if len(subjects) >= len(SUBJECTS):
        earned.add("all_subjects")
    if streak >= 7:
        earned.add("streak_7")
    if streak >= 30:
        earned.add("streak_30")

    old = set(json.loads(stats["badges"] or "[]"))
    with get_db() as conn:
        conn.execute(
            "UPDATE user_stats SET badges=? WHERE username=?",
            (json.dumps(sorted(earned), ensure_ascii=False), u),
        )

    for badge in earned - old:
        if badge in BADGES:
            add_notification(u, "إنجاز جديد!", BADGES[badge], "🏆")
    return sorted(earned)


def get_user_badges(u):
    stats = get_user_stats(u)
    return [BADGES[b] for b in json.loads(stats["badges"] or "[]") if b in BADGES]


def add_notification(u, title, msg, icon="🔔"):
    with get_db() as conn:
        conn.execute("""
            INSERT INTO notifications(username, title, message, icon)
            VALUES (?, ?, ?, ?)
        """, (u, title, msg, icon))


def get_notifications(u, unread=False):
    with get_db() as conn:
        if unread:
            rows = conn.execute("""
                SELECT * FROM notifications WHERE username=? AND is_read=0
                ORDER BY id DESC
            """, (u,)).fetchall()
        else:
            rows = conn.execute("""
                SELECT * FROM notifications WHERE username=?
                ORDER BY id DESC LIMIT 100
            """, (u,)).fetchall()
    return [dict(r) for r in rows]


def mark_notifications_read(u):
    with get_db() as conn:
        conn.execute(
            "UPDATE notifications SET is_read=1 WHERE username=?", (u,)
        )


def check_daily_bonus(u):
    today = datetime.date.today()
    today_str = today.isoformat()
    yesterday_str = (today - datetime.timedelta(days=1)).isoformat()

    with get_db() as conn:
        conn.execute("INSERT OR IGNORE INTO user_stats(username) VALUES (?)", (u,))
        row = conn.execute(
            "SELECT last_daily, streak FROM user_stats WHERE username=?", (u,)
        ).fetchone()

        if row["last_daily"] == today_str:
            return 0

        streak = int(row["streak"]) + 1 if row["last_daily"] == yesterday_str else 1
        bonus = min(50, 10 + (streak - 1) * 5)
        current = conn.execute(
            "SELECT total_points FROM user_stats WHERE username=?", (u,)
        ).fetchone()["total_points"]
        total = int(current) + bonus

        conn.execute("""
            UPDATE user_stats SET last_daily=?, streak=?, total_points=?, level=?
            WHERE username=?
        """, (today_str, streak, total, total // 100 + 1, u))

    add_notification(u, "المكافأة اليومية", f"حصلت على {bonus} نقطة! سلسلة الأيام: {streak}.", "🎁")
    check_badges(u)
    return bonus


def get_rank(lvl):
    result = RANKS[1]
    for threshold, rank in sorted(RANKS.items()):
        if lvl >= threshold:
            result = rank
    return result


def toggle_favorite(u, lid):
    with get_db() as conn:
        row = conn.execute(
            "SELECT id FROM favorites WHERE username=? AND lesson_id=?", (u, lid)
        ).fetchone()
        if row:
            conn.execute("DELETE FROM favorites WHERE id=?", (row["id"],))
            return False
        conn.execute(
            "INSERT OR IGNORE INTO favorites(username, lesson_id) VALUES (?, ?)",
            (u, lid),
        )
        return True


def is_favorite(u, lid):
    with get_db() as conn:
        return conn.execute(
            "SELECT 1 FROM favorites WHERE username=? AND lesson_id=?", (u, lid)
        ).fetchone() is not None


def get_favorites(u):
    with get_db() as conn:
        rows = conn.execute("""
            SELECT l.* FROM lessons l JOIN favorites f ON l.id=f.lesson_id
            WHERE f.username=? ORDER BY f.id DESC
        """, (u,)).fetchall()
    return [dict(r) for r in rows]


def load_lessons(subject=None, language=None, owner=None, search=None):
    query = "SELECT * FROM lessons WHERE 1=1"
    args = []
    if subject and subject != "all":
        query += " AND subject=?"
        args.append(subject)
    if language and language != "all":
        query += " AND language=?"
        args.append(language)
    if owner and owner != "all":
        query += " AND owner=?"
        args.append(owner)
    if search:
        query += " AND (title LIKE ? OR content LIKE ?)"
        args.extend([f"%{search}%", f"%{search}%"])
    query += " ORDER BY id DESC"
    with get_db() as conn:
        rows = conn.execute(query, args).fetchall()
    return [dict(r) for r in rows]


def add_lesson(subject, language, title, content, image_url="", pdf_url="", owner=None):
    owner = owner or st.session_state.get("username", "soufianeDEV")
    with get_db() as conn:
        cur = conn.execute("""
            INSERT INTO lessons(subject, language, title, content, image_url, pdf_url, owner, created_at)
            VALUES (?, ?, ?, ?, ?, ?, ?, ?)
        """, (
            subject, language, title.strip(), content.strip(), image_url.strip(),
            pdf_url.strip(), owner, datetime.datetime.now().isoformat(timespec="seconds"),
        ))
        return cur.lastrowid


def delete_lesson(lid):
    with get_db() as conn:
        conn.execute("DELETE FROM lessons WHERE id=?", (lid,))


def load_questions(lid):
    with get_db() as conn:
        rows = conn.execute(
            "SELECT * FROM questions WHERE lesson_id=? ORDER BY id", (lid,)
        ).fetchall()
    return [dict(r) for r in rows]


def add_question(lid, question, a, b, c, d, correct, explanation=""):
    if correct not in ("A", "B", "C", "D"):
        raise ValueError("La bonne réponse doit être A, B, C ou D.")
    with get_db() as conn:
        conn.execute("""
            INSERT INTO questions
            (lesson_id, question, option_a, option_b, option_c, option_d, correct_answer, explanation)
            VALUES (?, ?, ?, ?, ?, ?, ?, ?)
        """, (lid, question, a, b, c, d, correct, explanation))


def delete_question(qid):
    with get_db() as conn:
        conn.execute("DELETE FROM questions WHERE id=?", (qid,))


def upload_file(f, folder):
    if f is None:
        return ""
    folder = os.path.basename(folder)
    destination = Path(UPLOAD_DIR) / folder
    destination.mkdir(parents=True, exist_ok=True)
    safe_name = os.path.basename(f.name).replace(" ", "_")
    target = destination / safe_name
    with open(target, "wb") as output:
        output.write(f.getbuffer())
    return str(target)


def render_pdf(path):
    if not path:
        st.info("لا يوجد ملف PDF لهذا الدرس.")
        return
    if str(path).startswith(("http://", "https://")):
        st.link_button("📄 فتح ملف PDF", path)
        return
    if not os.path.isfile(path):
        st.warning("ملف PDF غير موجود.")
        return
    with open(path, "rb") as file:
        data = base64.b64encode(file.read()).decode("utf-8")
    st.markdown(
        f'<iframe src="data:application/pdf;base64,{data}" '
        'width="100%" height="650" type="application/pdf"></iframe>',
        unsafe_allow_html=True,
    )


def add_review(lid, u, rating, comment):
    with get_db() as conn:
        conn.execute("""
            INSERT INTO reviews(lesson_id, username, rating, comment)
            VALUES (?, ?, ?, ?)
            ON CONFLICT(lesson_id, username)
            DO UPDATE SET rating=excluded.rating, comment=excluded.comment
        """, (lid, u, int(rating), comment.strip()))


def get_reviews(lid):
    with get_db() as conn:
        rows = conn.execute(
            "SELECT * FROM reviews WHERE lesson_id=? ORDER BY id DESC", (lid,)
        ).fetchall()
    return [dict(r) for r in rows]


def get_avg_rating(lid):
    with get_db() as conn:
        row = conn.execute(
            "SELECT AVG(rating) AS avg, COUNT(*) AS n FROM reviews WHERE lesson_id=?",
            (lid,),
        ).fetchone()
    return (round(row["avg"], 1) if row["avg"] is not None else 0, row["n"])


def add_message(lid, u, message):
    with get_db() as conn:
        conn.execute("""
            INSERT INTO messages(lesson_id, username, message, created_at)
            VALUES (?, ?, ?, ?)
        """, (lid, u, message.strip(), datetime.datetime.now().isoformat(timespec="seconds")))


def get_messages(lid):
    with get_db() as conn:
        rows = conn.execute(
            "SELECT * FROM messages WHERE lesson_id=? ORDER BY id DESC LIMIT 100",
            (lid,),
        ).fetchall()
    return [dict(r) for r in rows]


def add_flashcard(u, subject, front, back):
    with get_db() as conn:
        conn.execute("""
            INSERT INTO flashcards(username, subject, front, back)
            VALUES (?, ?, ?, ?)
        """, (u, subject, front.strip(), back.strip()))


def get_flashcards(u, s=None):
    with get_db() as conn:
        if s and s != "all":
            rows = conn.execute("""
                SELECT * FROM flashcards WHERE username=? AND subject=? ORDER BY id DESC
            """, (u, s)).fetchall()
        else:
            rows = conn.execute(
                "SELECT * FROM flashcards WHERE username=? ORDER BY id DESC", (u,)
            ).fetchall()
    return [dict(r) for r in rows]


def delete_flashcard(fid):
    with get_db() as conn:
        conn.execute("DELETE FROM flashcards WHERE id=?", (fid,))


def toggle_flashcard_known(fid):
    with get_db() as conn:
        conn.execute(
            "UPDATE flashcards SET known=1-known WHERE id=?", (fid,)
        )


def add_note(u, lid, note):
    with get_db() as conn:
        conn.execute("""
            INSERT INTO notes(username, lesson_id, note, created_at)
            VALUES (?, ?, ?, ?)
        """, (u, lid, note.strip(), datetime.datetime.now().isoformat(timespec="seconds")))


def get_notes(u, lid):
    with get_db() as conn:
        rows = conn.execute("""
            SELECT * FROM notes WHERE username=? AND lesson_id=? ORDER BY id DESC
        """, (u, lid)).fetchall()
    return [dict(r) for r in rows]


def delete_note(nid):
    with get_db() as conn:
        conn.execute("DELETE FROM notes WHERE id=?", (nid,))


def add_friend(u, fu):
    fu = fu.strip()
    if u == fu:
        return False, "لا يمكنك إضافة نفسك."
    with get_db() as conn:
        exists = conn.execute(
            "SELECT 1 FROM users WHERE username=?", (fu,)
        ).fetchone()
        if not exists:
            return False, "اسم المستخدم غير موجود."
        try:
            conn.execute("""
                INSERT INTO friends(username, friend_username, status)
                VALUES (?, ?, 'accepted')
            """, (u, fu))
            conn.execute("""
                INSERT OR IGNORE INTO friends(username, friend_username, status)
                VALUES (?, ?, 'accepted')
            """, (fu, u))
            return True, "تمت إضافة الصديق."
        except sqlite3.IntegrityError:
            return False, "هذا المستخدم موجود بالفعل في قائمة أصدقائك."


def get_friends(u):
    with get_db() as conn:
        rows = conn.execute(
            "SELECT * FROM friends WHERE username=? ORDER BY id DESC", (u,)
        ).fetchall()
    return [dict(r) for r in rows]


def remove_friend(u, fu):
    with get_db() as conn:
        conn.execute(
            "DELETE FROM friends WHERE username=? AND friend_username=?", (u, fu)
        )
        conn.execute(
            "DELETE FROM friends WHERE username=? AND friend_username=?", (fu, u)
        )


def add_study_plan(u, subject, priority, target_date):
    with get_db() as conn:
        conn.execute("""
            INSERT INTO study_plan(username, subject, priority, target_date)
            VALUES (?, ?, ?, ?)
        """, (u, subject, priority, str(target_date)))


def get_study_plan(u):
    with get_db() as conn:
        rows = conn.execute("""
            SELECT * FROM study_plan WHERE username=?
            ORDER BY completed ASC, target_date ASC, id DESC
        """, (u,)).fetchall()
    return [dict(r) for r in rows]


def toggle_study_plan(pid):
    with get_db() as conn:
        conn.execute(
            "UPDATE study_plan SET completed=1-completed WHERE id=?", (pid,)
        )


def auto_generate_plan(u):
    weaknesses = get_weaknesses(u)
    chosen = [w["subject"] for w in weaknesses]
    if not chosen:
        chosen = list(SUBJECTS.keys())
    today = datetime.date.today()
    count = 0
    for index, subject in enumerate(chosen[:7]):
        add_study_plan(
            u, subject, "high" if index == 0 else "normal",
            today + datetime.timedelta(days=index),
        )
        count += 1
    return count


# ============================================================
# THEME AND LANGUAGE
# ============================================================

def T(key):
    lang = st.session_state.get("language", "ar")
    return TRANSLATIONS.get(lang, TRANSLATIONS["ar"]).get(key, key)


def apply_theme():
    theme_name = st.session_state.get("theme", "🌙 Midnight Purple")
    theme = THEMES.get(theme_name, THEMES["🌙 Midnight Purple"])
    st.markdown(f"""
    <style>
    :root {{
        color-scheme: {"light" if theme_name == "☀️ Light Mode" else "dark"};
    }}
    .stApp {{
        background: {theme["bg"]};
        color: {theme["text"]};
        direction: rtl;
    }}
    [data-testid="stHeader"] {{
        background: {theme["bg"]};
    }}
    [data-testid="stSidebar"] {{
        background: {theme["secondary"]};
        border-left: 1px solid {theme["border"]};
        direction: rtl;
    }}
    [data-testid="stSidebar"] * {{
        text-align: right;
    }}
    .stMarkdown, .stText, p, label, h1, h2, h3, h4 {{
        color: {theme["text"]};
    }}
    .stButton button, .stDownloadButton button {{
        border-radius: 12px;
        border: 1px solid {theme["border"]};
        background: {theme["accent"]};
        color: white;
        font-weight: 700;
        width: 100%;
    }}
    .stButton button:hover {{
        border-color: {theme["highlight"]};
        color: {theme["text"]};
    }}
    [data-testid="stMetric"] {{
        background: {theme["card"]};
        border: 1px solid {theme["border"]};
        padding: 16px;
        border-radius: 16px;
    }}
    [data-testid="stExpander"] {{
        background: {theme["card"]};
        border-radius: 12px;
        border: 1px solid {theme["border"]};
    }}
    .rm-card {{
        background: {theme["card"]};
        border: 1px solid {theme["border"]};
        border-radius: 16px;
        padding: 18px;
        margin: 8px 0 16px 0;
    }}
    .rm-hero {{
        background: linear-gradient(135deg, {theme["secondary"]}, {theme["card"]});
        border: 1px solid {theme["border"]};
        border-radius: 22px;
        padding: 28px;
        text-align: center;
        margin-bottom: 20px;
    }}
    .rm-accent {{
        color: {theme["highlight"]};
        font-weight: 800;
    }}
    .rm-footer {{
        text-align: center;
        padding: 24px 0 8px 0;
        margin-top: 36px;
        border-top: 1px solid {theme["border"]};
        opacity: 0.8;
        font-size: 13px;
    }}
    input, textarea {{
        direction: rtl !important;
    }}
    div[data-testid="stForm"] {{
        border-color: {theme["border"]};
    }}
    </style>
    """, unsafe_allow_html=True)


def render_footer():
    st.markdown(
        '<div class="rm-footer">© 2026 Soufiane Ouhazza — 3AC RevisioMaroc</div>',
        unsafe_allow_html=True,
    )


def safe_rerun():
    st.rerun()


def login_user(user):
    st.session_state.authenticated = True
    st.session_state.username = user["username"]
    st.session_state.role = user["role"]
    st.session_state.full_name = user["full_name"]
    st.session_state.page = "home"
    st.session_state.quiz_answers = {}
    st.session_state.quiz_submitted = False
    st.session_state.quiz_started = None
    check_daily_bonus(user["username"])
    safe_rerun()


# ============================================================
# AUTHENTICATION PAGES
# ============================================================

def render_auth_home():
    st.markdown("""
    <div class="rm-hero">
        <h1>📚 3AC RevisioMaroc</h1>
        <h3>منصتك الذكية للنجاح في الثالثة إعدادي</h3>
        <p>تعلم، راجع، اختبر معلوماتك، واجمع النقاط والإنجازات!</p>
    </div>
    """, unsafe_allow_html=True)

    col1, col2, col3 = st.columns(3)
    with col1:
        st.markdown("### 🎓 تلميذ")
        st.write("ادخل إلى حسابك، راجع الدروس، وأنجز الاختبارات.")
        if st.button("دخول التلميذ", key="auth_student", use_container_width=True):
            st.session_state.auth_route = "student"
            safe_rerun()
    with col2:
        st.markdown("### 🛠️ مطور")
        st.write("إدارة الدروس والأسئلة والمحتوى التعليمي.")
        if st.button("دخول المطور", key="auth_developer", use_container_width=True):
            st.session_state.auth_route = "developer"
            safe_rerun()
    with col3:
        st.markdown("### ✨ حساب جديد")
        st.write("أنشئ حساباً مجانياً وابدأ رحلة المراجعة.")
        if st.button("إنشاء حساب", key="auth_register", use_container_width=True):
            st.session_state.auth_route = "register"
            safe_rerun()

    st.info("حساب المطور الافتراضي يُنشأ تلقائياً عند تهيئة قاعدة البيانات.")


def render_student_login():
    st.subheader("🎓 تسجيل دخول التلميذ")
    with st.form("student_login_form"):
        username = st.text_input("اسم المستخدم")
        password = st.text_input("كلمة المرور", type="password")
        submitted = st.form_submit_button("دخول")
    if submitted:
        user = authenticate(username, password)
        if user and user["role"] == "student":
            login_user(user)
        else:
            st.error("بيانات الدخول غير صحيحة أو الحساب ليس حساب تلميذ.")
    if st.button("⬅️ رجوع", key="student_back"):
        st.session_state.auth_route = "home"
        safe_rerun()


def render_developer_login():
    st.subheader("🛠️ دخول المطور")
    with st.form("developer_login_form"):
        username = st.text_input("اسم المستخدم")
        password = st.text_input("كلمة المرور", type="password")
        submitted = st.form_submit_button("دخول المطور")
    if submitted:
        user = authenticate(username, password)
        if user and user["role"] == "developer":
            login_user(user)
        else:
            st.error("بيانات المطور غير صحيحة.")
    if st.button("⬅️ رجوع", key="developer_back"):
        st.session_state.auth_route = "home"
        safe_rerun()


def render_register():
    st.subheader("✨ إنشاء حساب جديد")
    with st.form("register_form"):
        full_name = st.text_input("الاسم الكامل")
        username = st.text_input("اسم المستخدم")
        password = st.text_input("كلمة المرور", type="password")
        confirm = st.text_input("تأكيد كلمة المرور", type="password")
        submitted = st.form_submit_button("إنشاء الحساب")
    if submitted:
        if password != confirm:
            st.error("كلمتا المرور غير متطابقتين.")
        else:
            ok, msg = register_user(username, password, full_name)
            if ok:
                st.success(msg)
                st.session_state.auth_route = "student"
                safe_rerun()
            else:
                st.error(msg)
    if st.button("⬅️ رجوع", key="register_back"):
        st.session_state.auth_route = "home"
        safe_rerun()


def render_auth_page():
    apply_theme()
    route = st.session_state.get("auth_route", "home")
    if route == "student":
        render_student_login()
    elif route == "developer":
        render_developer_login()
    elif route == "register":
        render_register()
    else:
        render_auth_home()
    render_footer()


# ============================================================
# DASHBOARD
# ============================================================

def render_dashboard():
    u = st.session_state.username
    stats = get_user_stats(u)
    lessons = load_lessons()
    history = get_quiz_history(u, 5)
    unread = len(get_notifications(u, unread=True))

    st.markdown(f"""
    <div class="rm-hero">
        <h1>مرحباً، {st.session_state.full_name} 👋</h1>
        <h3>أهلاً بك في {APP_NAME}</h3>
        <p>رتبتك الحالية: <span class="rm-accent">{get_rank(stats["level"])}</span></p>
    </div>
    """, unsafe_allow_html=True)

    cols = st.columns(4)
    cols[0].metric("⭐ النقاط", stats["total_points"])
    cols[1].metric("🏅 المستوى", stats["level"])
    cols[2].metric("📝 الاختبارات", stats["quizzes_taken"])
    cols[3].metric("🔔 إشعارات غير مقروءة", unread)

    st.subheader("📚 المواد الدراسية")
    cards = st.columns(4)
    for i, (key, subject) in enumerate(SUBJECTS.items()):
        with cards[i % 4]:
            count = sum(1 for lesson in lessons if lesson["subject"] == key)
            st.markdown(f"""
            <div class="rm-card" style="border-top:4px solid {subject["color"]};">
                <h2>{subject["icon"]}</h2>
                <h4>{subject["name"]}</h4>
                <p>{count} درس</p>
            </div>
            """, unsafe_allow_html=True)
            if st.button("استكشف الدروس", key=f"subject_{key}"):
                st.session_state.selected_subject = key
                st.session_state.page = "lessons"
                safe_rerun()

    st.subheader("🕘 آخر الاختبارات")
    if history:
        st.dataframe(
            [{
                "الدرس": h["lesson_title"],
                "المادة": SUBJECTS.get(h["subject"], {}).get("name", h["subject"]),
                "النتيجة": f'{h["score"]}/{h["total"]}',
                "النسبة": f'{h["percent"]}%',
                "التاريخ": h["created_at"][:16],
            } for h in history],
            use_container_width=True,
            hide_index=True,
        )
    else:
        st.info("لم تنجز أي اختبار بعد. ابدأ الآن من صفحة الاختبارات.")

    st.subheader("⚡ اختصارات")
    a, b, c = st.columns(3)
    with a:
        if st.button("📝 بدء اختبار", use_container_width=True):
            st.session_state.page = "quiz"
            safe_rerun()
    with b:
        if st.button("🧠 مراجعة سريعة", use_container_width=True):
            st.session_state.page = "review"
            safe_rerun()
    with c:
        if st.button("📅 خطة المراجعة", use_container_width=True):
            st.session_state.page = "plan"
            safe_rerun()


# ============================================================
# LESSONS AND LESSON DETAILS
# ============================================================

def render_lessons():
    st.title("📚 مكتبة الدروس")
    col1, col2, col3 = st.columns([2, 1, 1])
    with col1:
        search = st.text_input("🔎 ابحث عن درس")
    with col2:
        subject = st.selectbox(
            "المادة",
            ["all"] + list(SUBJECTS.keys()),
            format_func=lambda x: "جميع المواد" if x == "all" else
            f'{SUBJECTS[x]["icon"]} {SUBJECTS[x]["name"]}',
            index=(["all"] + list(SUBJECTS.keys())).index(
                st.session_state.get("selected_subject", "all")
            ) if st.session_state.get("selected_subject", "all") in ["all"] + list(SUBJECTS.keys()) else 0,
        )
    with col3:
        language = st.selectbox(
            "لغة الدرس",
            ["all", "ar", "fr", "en"],
            format_func=lambda x: {"all": "الكل", "ar": "العربية", "fr": "Français", "en": "English"}[x],
        )

    lessons = load_lessons(subject, language, "all", search)
    if not lessons:
        st.info("لا توجد دروس مطابقة حالياً. يمكن للمطور إضافة دروس جديدة.")
    for lesson in lessons:
        _render_lesson_card(lesson)


def _render_lesson_card(lesson):
    lid = lesson["id"]
    u = st.session_state.username
    avg, count = get_avg_rating(lid)
    subject = SUBJECTS.get(lesson["subject"], {"name": lesson["subject"], "icon": "📘", "color": "#4A90E2"})

    with st.expander(f'{subject["icon"]} {lesson["title"]}  •  ⭐ {avg} ({count})'):
        tabs = st.tabs(["📖 الدرس", "📝 الاختبار", "⭐ التقييم", "💬 النقاش"])
        with tabs[0]:
            st.markdown(f'**المادة:** {subject["name"]}')
            st.markdown(lesson["content"])
            if lesson["image_url"]:
                if lesson["image_url"].startswith(("http://", "https://")):
                    st.image(lesson["image_url"], use_container_width=True)
                elif os.path.isfile(lesson["image_url"]):
                    st.image(lesson["image_url"], use_container_width=True)
            if lesson["pdf_url"]:
                render_pdf(lesson["pdf_url"])
            c1, c2 = st.columns(2)
            with c1:
                if is_favorite(u, lid):
                    label = "💔 إزالة من المفضلة"
                else:
                    label = "❤️ أضف إلى المفضلة"
                if st.button(label, key=f"fav_{lid}", use_container_width=True):
                    toggle_favorite(u, lid)
                    safe_rerun()
            with c2:
                if st.button("✍️ ملاحظاتي", key=f"notes_open_{lid}", use_container_width=True):
                    st.session_state.notes_lesson_id = lid
                    st.session_state.page = "notes"
                    safe_rerun()
        with tabs[1]:
            questions = load_questions(lid)
            if questions:
                if st.button("ابدأ اختبار هذا الدرس", key=f"quiz_lesson_{lid}"):
                    st.session_state.quiz_lesson_id = lid
                    st.session_state.page = "quiz"
                    st.session_state.quiz_started = time.time()
                    st.session_state.quiz_submitted = False
                    safe_rerun()
                st.caption(f"عدد الأسئلة: {len(questions)}")
            else:
                st.info("لم تتم إضافة أسئلة لهذا الدرس بعد.")
        with tabs[2]:
            _render_reviews(lid)
        with tabs[3]:
            _render_discussion(lid)


def _render_reviews(lid):
    u = st.session_state.username
    with st.form(f"review_form_{lid}"):
        rating = st.slider("تقييمك من 1 إلى 5", 1, 5, 5)
        comment = st.text_area("تعليقك (اختياري)")
        submitted = st.form_submit_button("حفظ التقييم")
    if submitted:
        add_review(lid, u, rating, comment)
        st.success("تم حفظ تقييمك.")
        safe_rerun()

    st.markdown("**تقييمات التلاميذ**")
    for review in get_reviews(lid):
        st.markdown(
            f'⭐ {review["rating"]}/5 — **{review["username"]}**  \n{review["comment"] or "بدون تعليق"}'
        )


def _render_discussion(lid):
    u = st.session_state.username
    with st.form(f"message_form_{lid}"):
        message = st.text_area("اكتب سؤالك أو تعليقك", max_chars=2000)
        submitted = st.form_submit_button("إرسال")
    if submitted and message.strip():
        add_message(lid, u, message)
        safe_rerun()

    for msg in get_messages(lid):
        st.markdown(
            f'<div class="rm-card"><b>{msg["username"]}</b><br>{msg["message"]}'
            f'<br><small>{msg["created_at"]}</small></div>',
            unsafe_allow_html=True,
        )


def _render_notes(lid):
    u = st.session_state.username
    st.subheader("📝 ملاحظاتي الشخصية")
    with st.form(f"note_form_{lid}"):
        note = st.text_area("أضف ملاحظة لهذا الدرس")
        submitted = st.form_submit_button("حفظ الملاحظة")
    if submitted and note.strip():
        add_note(u, lid, note)
        st.success("تم حفظ الملاحظة.")
        safe_rerun()
    for item in get_notes(u, lid):
        with st.container(border=True):
            st.write(item["note"])
            st.caption(item["created_at"])
            if st.button("🗑️ حذف", key=f"note_del_{item['id']}"):
                delete_note(item["id"])
                safe_rerun()


# ============================================================
# QUIZ
# ============================================================

def render_quiz():
    st.title("📝 الاختبارات")
    u = st.session_state.username

    lessons = load_lessons()
    if not lessons:
        st.info("لا توجد دروس بعد. أضف دروساً وأسئلة من لوحة المطور.")
        return

    lesson_map = {f'{x["title"]} — {SUBJECTS.get(x["subject"], {}).get("name", x["subject"])} (ID {x["id"]})': x for x in lessons}
    labels = list(lesson_map.keys())

    default_index = 0
    existing_id = st.session_state.get("quiz_lesson_id")
    for i, item in enumerate(lesson_map.values()):
        if item["id"] == existing_id:
            default_index = i
            break

    selected_label = st.selectbox("اختر الدرس", labels, index=default_index)
    lesson = lesson_map[selected_label]
    lid = lesson["id"]
    questions = load_questions(lid)

    if not questions:
        st.warning("هذا الدرس لا يحتوي على أسئلة.")
        return

    _render_quiz_ui(questions, lid)


def _render_quiz_ui(questions, lesson_id):
    u = st.session_state.username
    with get_db() as conn:
        lesson = conn.execute("SELECT * FROM lessons WHERE id=?", (lesson_id,)).fetchone()
    if not lesson:
        st.error("الدرس غير موجود.")
        return

    if "quiz_started" not in st.session_state or st.session_state.quiz_started is None:
        st.session_state.quiz_started = time.time()
    if "quiz_answers" not in st.session_state:
        st.session_state.quiz_answers = {}
    if "quiz_submitted" not in st.session_state:
        st.session_state.quiz_submitted = False

    elapsed = int(time.time() - st.session_state.quiz_started)
    remaining = max(0, 600 - elapsed)
    st.progress(remaining / 600)
    st.markdown(f"### ⏱️ الوقت المتبقي: {remaining // 60:02d}:{remaining % 60:02d}")
    st.caption("مدة الاختبار 10 دقائق. يتم التصحيح عند الإرسال.")

    if remaining <= 0 and not st.session_state.quiz_submitted:
        st.warning("انتهى الوقت. أرسل إجاباتك للتصحيح.")

    if st.session_state.quiz_submitted:
        result_key = f"quiz_result_{lesson_id}"
        result = st.session_state.get(result_key)
        if result:
            st.success(f'النتيجة: {result["score"]}/{result["total"]} — {result["percent"]}%')
            for i, q in enumerate(questions):
                chosen = result["answers"].get(str(q["id"]), "")
                correct = q["correct_answer"]
                options = {
                    "A": q["option_a"], "B": q["option_b"],
                    "C": q["option_c"], "D": q["option_d"],
                }
                st.markdown(f'**السؤال {i+1}:** {q["question"]}')
                st.write(f'إجابتك: {options.get(chosen, "لم تجب")}')
                st.write(f'الإجابة الصحيحة: {options.get(correct, correct)}')
                if q["explanation"]:
                    st.info(q["explanation"])
            if st.button("🔄 اختبار جديد"):
                st.session_state.quiz_started = time.time()
                st.session_state.quiz_answers = {}
                st.session_state.quiz_submitted = False
                st.session_state.pop(result_key, None)
                safe_rerun()
            return

    answers = {}
    with st.form(f"quiz_form_{lesson_id}"):
        for i, q in enumerate(questions):
            st.markdown(f"#### السؤال {i + 1}")
            st.write(q["question"])
            opts = {
                "A": q["option_a"], "B": q["option_b"],
                "C": q["option_c"], "D": q["option_d"],
            }
            available = {k: v for k, v in opts.items() if v and v.strip()}
            choices = ["بدون إجابة"] + [f"{k} — {v}" for k, v in available.items()]
            chosen = st.radio(
                f"اختر إجابتك للسؤال {i+1}",
                choices,
                key=f"answer_{lesson_id}_{q['id']}",
                index=0,
            )
            answer_letter = chosen.split(" — ", 1)[0] if chosen != "بدون إجابة" else ""
            answers[str(q["id"])] = answer_letter
            st.divider()
        submitted = st.form_submit_button("✅ إنهاء الاختبار وتصحيح الإجابات")

    if submitted:
        score = sum(
            1 for q in questions
            if answers.get(str(q["id"])) == q["correct_answer"]
        )
        percent = save_quiz_result(
            u, lesson_id, lesson["title"], lesson["subject"], score, len(questions)
        )
        st.session_state[f"quiz_result_{lesson_id}"] = {
            "score": score,
            "total": len(questions),
            "percent": percent,
            "answers": answers,
        }
        st.session_state.quiz_submitted = True
        st.session_state.quiz_answers = answers
        safe_rerun()


# ============================================================
# QUICK REVIEW AND FLASHCARDS
# ============================================================

def render_quick_review():
    st.title("⚡ مراجعة سريعة")
    u = st.session_state.username
    history = get_quiz_history(u, 100)
    if not history:
        st.info("أنجز اختباراً واحداً على الأقل لتظهر نتائجك هنا.")
    else:
        weaknesses = get_weaknesses(u)
        if weaknesses:
            st.subheader("🎯 المواد التي تحتاج إلى مراجعة")
            for item in weaknesses:
                name = SUBJECTS.get(item["subject"], {}).get("name", item["subject"])
                st.warning(f'{name}: متوسط النتائج {item["average"]:.1f}%')
        else:
            st.success("أداء جيد! لا توجد مواد بمتوسط أقل من 70%.")

        st.subheader("📈 نتائجك الأخيرة")
        for item in history[:10]:
            st.markdown(
                f'**{item["lesson_title"]}** — {item["score"]}/{item["total"]} '
                f'({item["percent"]}%)'
            )

    st.subheader("🎲 سؤال عشوائي")
    questions = []
    for lesson in load_lessons():
        for q in load_questions(lesson["id"]):
            q["lesson_title"] = lesson["title"]
            questions.append(q)
    if questions:
        if st.button("اختيار سؤال عشوائي"):
            st.session_state.random_question = random.choice(questions)
        q = st.session_state.get("random_question")
        if q:
            st.markdown(f'### {q["question"]}')
            opts = [
                ("A", q["option_a"]), ("B", q["option_b"]),
                ("C", q["option_c"]), ("D", q["option_d"]),
            ]
            opts = [(k, v) for k, v in opts if v]
            choice = st.radio(
                "الإجابة",
                [f"{k} — {v}" for k, v in opts],
                key=f"random_answer_{q['id']}",
            )
            if st.button("تحقق من الإجابة"):
                answer = choice.split(" — ", 1)[0]
                if answer == q["correct_answer"]:
                    st.success("إجابة صحيحة! 🎉")
                else:
                    st.error(f'الإجابة الصحيحة هي {q["correct_answer"]}.')
                if q["explanation"]:
                    st.info(q["explanation"])
    else:
        st.info("أضف أسئلة إلى الدروس لاستخدام المراجعة العشوائية.")

    st.subheader("🧠 إنشاء بطاقة حفظ")
    with st.form("quick_flashcard"):
        subject = st.selectbox(
            "المادة", list(SUBJECTS),
            format_func=lambda x: f'{SUBJECTS[x]["icon"]} {SUBJECTS[x]["name"]}',
        )
        front = st.text_input("السؤال أو المصطلح")
        back = st.text_area("الجواب أو التعريف")
        submitted = st.form_submit_button("إضافة البطاقة")
    if submitted and front.strip() and back.strip():
        add_flashcard(u, subject, front, back)
        st.success("تمت إضافة البطاقة.")


def render_flashcards():
    st.title("🧠 بطاقات الحفظ")
    u = st.session_state.username

    with st.expander("➕ إنشاء بطاقة جديدة"):
        with st.form("flashcard_create"):
            subject = st.selectbox(
                "المادة", list(SUBJECTS),
                format_func=lambda x: f'{SUBJECTS[x]["icon"]} {SUBJECTS[x]["name"]}',
            )
            front = st.text_area("الوجه الأمامي")
            back = st.text_area("الوجه الخلفي")
            submitted = st.form_submit_button("حفظ")
        if submitted and front.strip() and back.strip():
            add_flashcard(u, subject, front, back)
            safe_rerun()

    selected_subject = st.selectbox(
        "تصفية حسب المادة", ["all"] + list(SUBJECTS),
        format_func=lambda x: "كل المواد" if x == "all" else SUBJECTS[x]["name"],
    )
    cards = get_flashcards(u, selected_subject)
    if not cards:
        st.info("لا توجد بطاقات بعد.")
        return

    index = st.selectbox(
        "اختر بطاقة",
        range(len(cards)),
        format_func=lambda i: f'{i+1}. {cards[i]["front"][:60]}',
    )
    card = cards[index]
    st.markdown(f"""
    <div class="rm-hero">
        <h3>❓ السؤال</h3>
        <p>{card["front"]}</p>
    </div>
    """, unsafe_allow_html=True)

    key = f"show_back_{card['id']}"
    if st.button("👁️ إظهار الجواب", key=f"reveal_{card['id']}"):
        st.session_state[key] = not st.session_state.get(key, False)
    if st.session_state.get(key, False):
        st.markdown(f"""
        <div class="rm-card">
            <h3>✅ الجواب</h3>
            <p>{card["back"]}</p>
        </div>
        """, unsafe_allow_html=True)

    c1, c2 = st.columns(2)
    with c1:
        label = "✅ أعرفها" if not card["known"] else "↩️ أراجعها مجدداً"
        if st.button(label, key=f"known_{card['id']}"):
            toggle_flashcard_known(card["id"])
            safe_rerun()
    with c2:
        if st.button("🗑️ حذف البطاقة", key=f"delete_fc_{card['id']}"):
            delete_flashcard(card["id"])
            safe_rerun()

    known = sum(1 for item in cards if item["known"])
    st.progress(known / len(cards))
    st.caption(f"بطاقات معروفة: {known}/{len(cards)}")


# ============================================================
# STUDY PLAN
# ============================================================

def render_study_plan():
    st.title("📅 خطة المراجعة")
    u = st.session_state.username

    c1, c2 = st.columns(2)
    with c1:
        if st.button("✨ إنشاء خطة تلقائية"):
            n = auto_generate_plan(u)
            st.success(f"تم إنشاء {n} مهام للمراجعة.")
            safe_rerun()
    with c2:
        if st.button("➕ إضافة مهمة"):
            st.session_state.show_plan_form = True

    if st.session_state.get("show_plan_form"):
        with st.form("study_plan_form"):
            subject = st.selectbox(
                "المادة", list(SUBJECTS),
                format_func=lambda x: SUBJECTS[x]["name"],
            )
            priority = st.selectbox("الأولوية", ["high", "normal", "low"],
                                    format_func=lambda x: {"high": "عالية", "normal": "عادية", "low": "منخفضة"}[x])
            target = st.date_input("تاريخ الإنجاز", value=datetime.date.today())
            submitted = st.form_submit_button("إضافة")
        if submitted:
            add_study_plan(u, subject, priority, target)
            st.session_state.show_plan_form = False
            safe_rerun()

    plans = get_study_plan(u)
    if not plans:
        st.info("خطتك فارغة. أضف مهاماً أو أنشئ خطة تلقائية.")
        return

    done = sum(1 for p in plans if p["completed"])
    st.progress(done / len(plans))
    st.caption(f"أكملت {done} من {len(plans)} مهمة.")

    for plan in plans:
        subject = SUBJECTS.get(plan["subject"], {"name": plan["subject"], "icon": "📚"})
        cols = st.columns([0.6, 4, 1.5, 1])
        with cols[0]:
            st.write("✅" if plan["completed"] else "⬜")
        with cols[1]:
            st.write(f'{subject["icon"]} {subject["name"]}')
            st.caption(f'الموعد: {plan["target_date"]} • الأولوية: {plan["priority"]}')
        with cols[2]:
            st.write("مكتملة" if plan["completed"] else "قيد الإنجاز")
        with cols[3]:
            if st.button("تغيير", key=f"plan_toggle_{plan['id']}"):
                toggle_study_plan(plan["id"])
                safe_rerun()


# ============================================================
# FRIENDS, LEADERBOARD, REPORTS, NOTIFICATIONS
# ============================================================

def render_friends():
    st.title("👥 الأصدقاء")
    u = st.session_state.username
    with st.form("add_friend_form"):
        friend = st.text_input("اسم المستخدم للصديق")
        submitted = st.form_submit_button("إضافة صديق")
    if submitted:
        ok, msg = add_friend(u, friend)
        (st.success if ok else st.error)(msg)

    friends = get_friends(u)
    if not friends:
        st.info("قائمة الأصدقاء فارغة.")
    for friend in friends:
        c1, c2 = st.columns([4, 1])
        c1.write(f'👤 {friend["friend_username"]}')
        if c2.button("إزالة", key=f'remove_friend_{friend["friend_username"]}'):
            remove_friend(u, friend["friend_username"])
            safe_rerun()


def render_leaderboard():
    st.title("🏆 لوحة المتصدرين")
    period = st.selectbox(
        "الفترة", ["all", "week", "month"],
        format_func=lambda x: {"all": "كل الوقت", "week": "آخر 7 أيام", "month": "آخر 30 يوماً"}[x],
    )
    board = get_leaderboard(period)
    if not board:
        st.info("لا توجد نتائج في هذه الفترة.")
        return
    for i, row in enumerate(board, 1):
        medal = {1: "🥇", 2: "🥈", 3: "🥉"}.get(i, f"{i}.")
        st.markdown(
            f'<div class="rm-card"><b>{medal} {row["username"]}</b>'
            f'<br>⭐ النقاط: {row["points"]}'
            f'<br>📝 الاختبارات: {row["quizzes"]}</div>',
            unsafe_allow_html=True,
        )


def render_weekly_report():
    st.title("📊 التقرير الأسبوعي")
    u = st.session_state.username
    report = get_weekly_report(u)
    c1, c2, c3, c4 = st.columns(4)
    c1.metric("الاختبارات", report["quizzes"])
    c2.metric("الإجابات الصحيحة", report["correct"])
    c3.metric("مجموع الأسئلة", report["questions"])
    c4.metric("متوسط النتائج", f'{report["average"]:.1f}%')

    st.subheader("📚 حسب المادة")
    subject_stats = get_subject_stats(u)
    if subject_stats:
        st.dataframe([{
            "المادة": SUBJECTS.get(x["subject"], {}).get("name", x["subject"]),
            "الاختبارات": x["quizzes"],
            "المتوسط": f'{x["average"]:.1f}%' if x["average"] is not None else "—",
            "أفضل نتيجة": f'{x["best"]:.1f}%' if x["best"] is not None else "—",
        } for x in subject_stats], use_container_width=True, hide_index=True)
    else:
        st.info("لا تتوفر بيانات كافية بعد.")


def render_notifications():
    st.title("🔔 الإشعارات")
    u = st.session_state.username
    notifications = get_notifications(u)
    if st.button("✓ وضع الكل كمقروء"):
        mark_notifications_read(u)
        safe_rerun()
    if not notifications:
        st.info("لا توجد إشعارات.")
        return
    for n in notifications:
        state = "🟢" if not n["is_read"] else "⚪"
        st.markdown(f"""
        <div class="rm-card">
            <h4>{state} {n["icon"]} {n["title"]}</h4>
            <p>{n["message"]}</p>
        </div>
        """, unsafe_allow_html=True)


def render_my_stats():
    st.title("📈 إحصائياتي")
    u = st.session_state.username
    stats = get_user_stats(u)
    c1, c2, c3 = st.columns(3)
    c1.metric("⭐ النقاط", stats["total_points"])
    c2.metric("🏅 المستوى", stats["level"])
    c3.metric("🔥 سلسلة الأيام", stats["streak"])
    st.markdown(f"### اللقب: {get_rank(stats['level'])}")
    st.progress((stats["total_points"] % 100) / 100)
    st.caption(f'التقدم نحو المستوى التالي: {stats["total_points"] % 100}/100 نقطة')

    st.subheader("🏆 الإنجازات")
    earned = json.loads(stats["badges"] or "[]")
    cols = st.columns(3)
    for i, (key, label) in enumerate(BADGES.items()):
        with cols[i % 3]:
            if key in earned:
                st.success(label)
            else:
                st.markdown(f"🔒 {label}")

    st.subheader("📚 المواد التي درستها")
    subjects = json.loads(stats["unique_subjects"] or "[]")
    for key in subjects:
        if key in SUBJECTS:
            st.write(f'{SUBJECTS[key]["icon"]} {SUBJECTS[key]["name"]}')


def render_favorites():
    st.title("❤️ دروسي المفضلة")
    favorites = get_favorites(st.session_state.username)
    if not favorites:
        st.info("لم تضف أي درس إلى المفضلة بعد.")
    for lesson in favorites:
        with st.expander(lesson["title"]):
            st.markdown(lesson["content"])
            if st.button("إزالة من المفضلة", key=f"remove_favorite_{lesson['id']}"):
                toggle_favorite(st.session_state.username, lesson["id"])
                safe_rerun()


# ============================================================
# DEVELOPER PANEL
# ============================================================

def render_developer_panel():
    st.title("🛠️ لوحة المطور")
    st.caption("إدارة الدروس والأسئلة التعليمية.")

    tabs = st.tabs(["➕ إضافة درس", "📝 إضافة أسئلة", "📚 إدارة الدروس", "📊 إحصائيات"])

    with tabs[0]:
        with st.form("developer_add_lesson"):
            subject = st.selectbox(
                "المادة", list(SUBJECTS),
                format_func=lambda x: f'{SUBJECTS[x]["icon"]} {SUBJECTS[x]["name"]}',
            )
            language = st.selectbox("اللغة", ["ar", "fr", "en"],
                                    format_func=lambda x: {"ar": "العربية", "fr": "Français", "en": "English"}[x])
            title = st.text_input("عنوان الدرس")
            content = st.text_area("محتوى الدرس (يدعم Markdown)", height=250)
            image_url = st.text_input("رابط الصورة (اختياري)")
            pdf_url = st.text_input("رابط PDF (اختياري)")
            uploaded_image = st.file_uploader("أو ارفع صورة", type=["png", "jpg", "jpeg", "webp"])
            uploaded_pdf = st.file_uploader("أو ارفع ملف PDF", type=["pdf"])
            submitted = st.form_submit_button("💾 حفظ الدرس")

        if submitted:
            if not title.strip() or not content.strip():
                st.error("العنوان والمحتوى مطلوبان.")
            else:
                if uploaded_image:
                    image_url = upload_file(uploaded_image, "images")
                if uploaded_pdf:
                    pdf_url = upload_file(uploaded_pdf, "pdfs")
                lid = add_lesson(subject, language, title, content, image_url, pdf_url)
                add_notification(
                    st.session_state.username, "تم إنشاء درس",
                    f"تمت إضافة الدرس: {title}", "📚",
                )
                st.success(f"تم حفظ الدرس بنجاح. رقم الدرس: {lid}")
                safe_rerun()

    with tabs[1]:
        lessons = load_lessons()
        if not lessons:
            st.info("أضف درساً أولاً.")
        else:
            lesson_map = {f'{x["title"]} (ID {x["id"]})': x for x in lessons}
            selected = st.selectbox("اختر الدرس", list(lesson_map.keys()), key="dev_question_lesson")
            lesson = lesson_map[selected]
            with st.form("developer_add_question"):
                question = st.text_area("نص السؤال")
                a = st.text_input("الخيار A")
                b = st.text_input("الخيار B")
                c = st.text_input("الخيار C")
                d = st.text_input("الخيار D")
                correct = st.selectbox("الإجابة الصحيحة", ["A", "B", "C", "D"])
                explanation = st.text_area("شرح الإجابة")
                submitted = st.form_submit_button("إضافة السؤال")
            if submitted:
                if not question.strip() or not a.strip() or not b.strip():
                    st.error("السؤال والخياران A وB مطلوبان.")
                else:
                    add_question(
                        lesson["id"], question, a, b, c, d, correct, explanation
                    )
                    st.success("تمت إضافة السؤال.")
                    safe_rerun()

            st.markdown("**الأسئلة الموجودة**")
            for q in load_questions(lesson["id"]):
                with st.container(border=True):
                    st.write(q["question"])
                    st.caption(f'الإجابة الصحيحة: {q["correct_answer"]}')
                    if st.button("حذف السؤال", key=f'delete_question_{q["id"]}'):
                        delete_question(q["id"])
                        safe_rerun()

    with tabs[2]:
        lessons = load_lessons()
        if not lessons:
            st.info("لا توجد دروس.")
        for lesson in lessons:
            with st.expander(f'{lesson["title"]} — {lesson["id"]}'):
                st.write(SUBJECTS.get(lesson["subject"], {}).get("name", lesson["subject"]))
                st.write(lesson["content"][:500])
                st.caption(f'المالك: {lesson["owner"]}')
                if st.button("🗑️ حذف الدرس", key=f'delete_lesson_{lesson["id"]}'):
                    delete_lesson(lesson["id"])
                    safe_rerun()

    with tabs[3]:
        with get_db() as conn:
            users_count = conn.execute("SELECT COUNT(*) FROM users").fetchone()[0]
            lessons_count = conn.execute("SELECT COUNT(*) FROM lessons").fetchone()[0]
            questions_count = conn.execute("SELECT COUNT(*) FROM questions").fetchone()[0]
            quizzes_count = conn.execute("SELECT COUNT(*) FROM quiz_history").fetchone()[0]
        a, b, c, d = st.columns(4)
        a.metric("المستخدمون", users_count)
        b.metric("الدروس", lessons_count)
        c.metric("الأسئلة", questions_count)
        d.metric("الاختبارات المنجزة", quizzes_count)


# ============================================================
# SIDEBAR AND ROUTING
# ============================================================

def render_sidebar():
    with st.sidebar:
        st.markdown("## 📚 RevisioMaroc")
        st.caption(f'{st.session_state.full_name} (@{st.session_state.username})')

        st.selectbox("🎨 " + T("theme"), list(THEMES.keys()), key="theme")
        st.selectbox(
            "🌐 " + T("language"),
            ["ar", "fr", "en"],
            format_func=lambda x: {"ar": "العربية", "fr": "Français", "en": "English"}[x],
            key="language",
        )
        apply_theme()
        st.divider()

        pages = [
            ("home", "🏠 " + T("home")),
            ("lessons", "📚 " + T("lessons")),
            ("quiz", "📝 " + T("quiz")),
            ("review", "⚡ " + T("review")),
            ("flashcards", "🧠 " + T("flashcards")),
            ("plan", "📅 " + T("plan")),
            ("friends", "👥 " + T("friends")),
            ("leaderboard", "🏆 " + T("leaderboard")),
            ("report", "📊 " + T("report")),
            ("notifications", "🔔 " + T("notifications")),
            ("stats", "📈 " + T("stats")),
            ("favorites", "❤️ " + T("favorites")),
            ("notes", "📝 ملاحظاتي"),
        ]
        if st.session_state.role == "developer":
            pages.append(("developer", "🛠️ " + T("developer")))

        for key, label in pages:
            if st.button(label, key=f"nav_{key}", use_container_width=True):
                st.session_state.page = key
                safe_rerun()

        st.divider()
        stats = get_user_stats(st.session_state.username)
        st.metric("⭐ النقاط", stats["total_points"])
        st.metric("🏅 المستوى", stats["level"])
        if st.button("🚪 " + T("logout"), use_container_width=True):
            for key in list(st.session_state.keys()):
                del st.session_state[key]
            st.session_state.authenticated = False
            st.session_state.auth_route = "home"
            safe_rerun()


def render_notes_page():
    st.title("📝 ملاحظاتي")
    lessons = load_lessons()
    if not lessons:
        st.info("لا توجد دروس لإضافة ملاحظات إليها.")
        return
    lesson_map = {f'{x["title"]} (ID {x["id"]})': x for x in lessons}
    labels = list(lesson_map.keys())
    default_index = 0
    selected_id = st.session_state.get("notes_lesson_id")
    for i, lesson in enumerate(lesson_map.values()):
        if lesson["id"] == selected_id:
            default_index = i
            break
    selected = st.selectbox("الدرس", labels, index=default_index)
    _render_notes(lesson_map[selected]["id"])


# ============================================================
# INITIALIZATION AND MAIN
# ============================================================

def main():
    init_db()

    defaults = {
        "authenticated": False,
        "auth_route": "home",
        "page": "home",
        "theme": "🌙 Midnight Purple",
        "language": "ar",
        "quiz_answers": {},
        "quiz_submitted": False,
        "quiz_started": None,
        "selected_subject": "all",
    }
    for key, value in defaults.items():
        if key not in st.session_state:
            st.session_state[key] = value

    apply_theme()

    if not st.session_state.authenticated:
        render_auth_page()
        st.stop()

    render_sidebar()
    apply_theme()

    page = st.session_state.get("page", "home")
    routes = {
        "home": render_dashboard,
        "lessons": render_lessons,
        "quiz": render_quiz,
        "review": render_quick_review,
        "flashcards": render_flashcards,
        "plan": render_study_plan,
        "friends": render_friends,
        "leaderboard": render_leaderboard,
        "report": render_weekly_report,
        "notifications": render_notifications,
        "stats": render_my_stats,
        "favorites": render_favorites,
        "notes": render_notes_page,
        "developer": render_developer_panel,
    }

    if page == "developer" and st.session_state.role != "developer":
        st.error("هذه الصفحة متاحة للمطور فقط.")
        st.session_state.page = "home"
        safe_rerun()

    render_function = routes.get(page, render_dashboard)
    render_function()
    render_footer()


if __name__ == "__main__":
    main()
