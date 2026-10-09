# ============================================================================
# 3AC RevisioMaroc - النسخة الأسطورية الكاملة
# © 2026 Soufiane Ouhazza
# ============================================================================
import streamlit as st
import hashlib, sqlite3, os, base64, random, time, json
from datetime import datetime, timedelta
from pathlib import Path

st.set_page_config(page_title="3AC RevisioMaroc", page_icon="🎓",
                   layout="wide", initial_sidebar_state="expanded")

DB_PATH = "revisiomaroc.db"
UPLOAD_DIR = Path("uploads"); UPLOAD_DIR.mkdir(exist_ok=True)

def get_db():
    conn = sqlite3.connect(DB_PATH, check_same_thread=False)
    conn.row_factory = sqlite3.Row
    return conn

def init_db():
    conn = get_db(); c = conn.cursor()
    c.execute("""CREATE TABLE IF NOT EXISTS users (id INTEGER PRIMARY KEY AUTOINCREMENT,
        username TEXT UNIQUE NOT NULL, password_hash TEXT NOT NULL,
        role TEXT NOT NULL DEFAULT 'student', full_name TEXT,
        created_at TEXT DEFAULT CURRENT_TIMESTAMP)""")
    c.execute("""CREATE TABLE IF NOT EXISTS lessons (id INTEGER PRIMARY KEY AUTOINCREMENT,
        subject TEXT NOT NULL, language TEXT NOT NULL, title TEXT NOT NULL,
        content TEXT, image_url TEXT, pdf_url TEXT,
        owner TEXT NOT NULL DEFAULT 'public', created_at TEXT DEFAULT CURRENT_TIMESTAMP)""")
    c.execute("""CREATE TABLE IF NOT EXISTS questions (id INTEGER PRIMARY KEY AUTOINCREMENT,
        lesson_id TEXT NOT NULL, question TEXT NOT NULL, option_a TEXT NOT NULL,
        option_b TEXT NOT NULL, option_c TEXT NOT NULL, option_d TEXT NOT NULL,
        correct_answer TEXT NOT NULL, explanation TEXT,
        created_at TEXT DEFAULT CURRENT_TIMESTAMP)""")
    c.execute("""CREATE TABLE IF NOT EXISTS quiz_history (id INTEGER PRIMARY KEY AUTOINCREMENT,
        username TEXT NOT NULL, lesson_id TEXT NOT NULL, lesson_title TEXT, subject TEXT,
        score INTEGER, total INTEGER, percent REAL,
        created_at TEXT DEFAULT CURRENT_TIMESTAMP)""")
    c.execute("""CREATE TABLE IF NOT EXISTS favorites (id INTEGER PRIMARY KEY AUTOINCREMENT,
        username TEXT NOT NULL, lesson_id INTEGER NOT NULL,
        created_at TEXT DEFAULT CURRENT_TIMESTAMP, UNIQUE(username, lesson_id))""")
    c.execute("""CREATE TABLE IF NOT EXISTS user_stats (id INTEGER PRIMARY KEY AUTOINCREMENT,
        username TEXT UNIQUE NOT NULL, total_points INTEGER DEFAULT 0,
        level INTEGER DEFAULT 1, quizzes_taken INTEGER DEFAULT 0,
        perfect_scores INTEGER DEFAULT 0, unique_subjects TEXT DEFAULT '',
        badges TEXT DEFAULT '', last_daily TEXT, streak INTEGER DEFAULT 0)""")
    c.execute("""CREATE TABLE IF NOT EXISTS reviews (id INTEGER PRIMARY KEY AUTOINCREMENT,
        lesson_id INTEGER NOT NULL, username TEXT NOT NULL,
        rating INTEGER CHECK(rating BETWEEN 1 AND 5), comment TEXT,
        created_at TEXT DEFAULT CURRENT_TIMESTAMP, UNIQUE(username, lesson_id))""")
    c.execute("""CREATE TABLE IF NOT EXISTS messages (id INTEGER PRIMARY KEY AUTOINCREMENT,
        lesson_id INTEGER, username TEXT NOT NULL, message TEXT NOT NULL,
        created_at TEXT DEFAULT CURRENT_TIMESTAMP)""")
    c.execute("""CREATE TABLE IF NOT EXISTS notifications (id INTEGER PRIMARY KEY AUTOINCREMENT,
        username TEXT NOT NULL, title TEXT, message TEXT, icon TEXT DEFAULT '🔔',
        is_read INTEGER DEFAULT 0, created_at TEXT DEFAULT CURRENT_TIMESTAMP)""")
    c.execute("""CREATE TABLE IF NOT EXISTS flashcards (id INTEGER PRIMARY KEY AUTOINCREMENT,
        username TEXT NOT NULL, subject TEXT, front TEXT NOT NULL,
        back TEXT NOT NULL, known INTEGER DEFAULT 0,
        created_at TEXT DEFAULT CURRENT_TIMESTAMP)""")
    c.execute("""CREATE TABLE IF NOT EXISTS notes (id INTEGER PRIMARY KEY AUTOINCREMENT,
        username TEXT NOT NULL, lesson_id INTEGER, note TEXT NOT NULL,
        created_at TEXT DEFAULT CURRENT_TIMESTAMP)""")
    c.execute("""CREATE TABLE IF NOT EXISTS friends (id INTEGER PRIMARY KEY AUTOINCREMENT,
        username TEXT NOT NULL, friend_username TEXT NOT NULL,
        status TEXT DEFAULT 'accepted', created_at TEXT DEFAULT CURRENT_TIMESTAMP,
        UNIQUE(username, friend_username))""")
    c.execute("""CREATE TABLE IF NOT EXISTS challenges (id INTEGER PRIMARY KEY AUTOINCREMENT,
        challenger TEXT NOT NULL, opponent TEXT NOT NULL, lesson_id TEXT,
        challenger_score INTEGER DEFAULT 0, opponent_score INTEGER DEFAULT 0,
        status TEXT DEFAULT 'pending', created_at TEXT DEFAULT CURRENT_TIMESTAMP)""")
    c.execute("""CREATE TABLE IF NOT EXISTS study_plan (id INTEGER PRIMARY KEY AUTOINCREMENT,
        username TEXT NOT NULL, subject TEXT, priority TEXT, target_date TEXT,
        completed INTEGER DEFAULT 0, created_at TEXT DEFAULT CURRENT_TIMESTAMP)""")

    c.execute("SELECT * FROM users WHERE username=?", ("soufianeDEV",))
    if not c.fetchone():
        dev_hash = hashlib.sha256("soufiane2030".encode()).hexdigest()
        c.execute("INSERT INTO users (username, password_hash, role, full_name) VALUES (?,?,?,?)",
                  ("soufianeDEV", dev_hash, "developer", "Soufiane Ouhazza"))
    conn.commit(); conn.close()

init_db()

def hash_password(p): return hashlib.sha256(p.encode()).hexdigest()

def register_user(u, p, n=""):
    if len(p) < 4: return False, "❌ كلمة المرور قصيرة"
    try:
        conn = get_db(); c = conn.cursor()
        c.execute("SELECT username FROM users WHERE username=?", (u,))
        if c.fetchone():
            conn.close(); return False, "❌ المستخدم موجود"
        c.execute("INSERT INTO users (username, password_hash, role, full_name) VALUES (?,?,?,?)",
                  (u, hash_password(p), "student", n or u))
        c.execute("INSERT OR IGNORE INTO user_stats (username) VALUES (?)", (u,))
        conn.commit(); conn.close()
        return True, "✅ تم"
    except Exception as e: return False, f"❌ {e}"

def authenticate(u, p):
    try:
        conn = get_db(); c = conn.cursor()
        c.execute("SELECT * FROM users WHERE username=?", (u,))
        row = c.fetchone(); conn.close()
        if not row: return False, None
        if row["password_hash"] == hash_password(p):
            return True, {"role": row["role"], "full_name": row["full_name"] or u}
        return False, None
    except Exception: return False, None

def get_user_stats(u):
    try:
        conn = get_db(); c = conn.cursor()
        c.execute("SELECT * FROM user_stats WHERE username=?", (u,))
        row = c.fetchone()
        if not row:
            c.execute("INSERT INTO user_stats (username) VALUES (?)", (u,))
            conn.commit()
            c.execute("SELECT * FROM user_stats WHERE username=?", (u,))
            row = c.fetchone()
        conn.close()
        return dict(row) if row else {}
    except Exception: return {}

def update_user_stats(u, points=0, quiz=False, perfect=False, subject=None):
    try:
        conn = get_db(); c = conn.cursor()
        c.execute("SELECT * FROM user_stats WHERE username=?", (u,))
        row = c.fetchone()
        if not row:
            c.execute("INSERT INTO user_stats (username) VALUES (?)", (u,))
            conn.commit()
            c.execute("SELECT * FROM user_stats WHERE username=?", (u,))
            row = c.fetchone()
        tp = row["total_points"] + points
        lvl = tp // 100 + 1
        q = row["quizzes_taken"] + (1 if quiz else 0)
        pf = row["perfect_scores"] + (1 if perfect else 0)
        subs = set(filter(None, (row["unique_subjects"] or "").split(",")))
        if subject: subs.add(subject)
        c.execute("""UPDATE user_stats SET total_points=?, level=?, quizzes_taken=?,
                     perfect_scores=?, unique_subjects=? WHERE username=?""",
                  (tp, lvl, q, pf, ",".join(subs), u))
        conn.commit(); conn.close()
        check_badges(u)
    except Exception: pass

def save_quiz_result(u, lid, lt, subj, score, total):
    try:
        pct = (score/total*100) if total > 0 else 0
        conn = get_db(); c = conn.cursor()
        c.execute("""INSERT INTO quiz_history (username, lesson_id, lesson_title, subject,
                     score, total, percent) VALUES (?,?,?,?,?,?,?)""",
                  (u, str(lid), lt, subj, score, total, pct))
        conn.commit(); conn.close()
    except Exception: pass

def get_quiz_history(u, limit=10):
    try:
        conn = get_db(); c = conn.cursor()
        c.execute("SELECT * FROM quiz_history WHERE username=? ORDER BY created_at DESC LIMIT ?", (u, limit))
        rows = [dict(r) for r in c.fetchall()]; conn.close()
        return rows
    except Exception: return []

def get_subject_stats(u):
    try:
        conn = get_db(); c = conn.cursor()
        c.execute("""SELECT subject, COUNT(*) as attempts, AVG(percent) as avg_percent,
                     MAX(percent) as best_percent FROM quiz_history WHERE username=?
                     GROUP BY subject""", (u,))
        rows = [dict(r) for r in c.fetchall()]; conn.close()
        return rows
    except Exception: return []

def get_weaknesses(u):
    try:
        conn = get_db(); c = conn.cursor()
        c.execute("""SELECT subject, AVG(percent) as avg, COUNT(*) as attempts
                     FROM quiz_history WHERE username=? GROUP BY subject
                     HAVING AVG(percent)<70 ORDER BY avg ASC""", (u,))
        rows = [dict(r) for r in c.fetchall()]; conn.close()
        return rows
    except Exception: return []

def get_leaderboard(period="week"):
    try:
        if period == "week":
            since = (datetime.now() - timedelta(days=7)).strftime("%Y-%m-%d")
        elif period == "month":
            since = (datetime.now() - timedelta(days=30)).strftime("%Y-%m-%d")
        else: since = "2000-01-01"
        conn = get_db(); c = conn.cursor()
        c.execute("""SELECT username, SUM(score*10) as points, COUNT(*) as quizzes,
                     AVG(percent) as avg_percent FROM quiz_history WHERE created_at>=?
                     GROUP BY username ORDER BY points DESC LIMIT 10""", (since,))
        rows = [dict(r) for r in c.fetchall()]; conn.close()
        return rows
    except Exception: return []

def get_weekly_report(u):
    try:
        wa = (datetime.now() - timedelta(days=7)).strftime("%Y-%m-%d")
        conn = get_db(); c = conn.cursor()
        c.execute("""SELECT COUNT(*) as quizzes, AVG(percent) as avg_percent,
                     SUM(score) as correct, SUM(total) as total_q FROM quiz_history
                     WHERE username=? AND created_at>=?""", (u, wa))
        row = c.fetchone(); conn.close()
        return dict(row) if row else {}
    except Exception: return {}

BADGES = {
    "first_quiz": {"icon":"🎯","name":"أول اختبار","desc":"أكملت أول اختبار"},
    "perfect": {"icon":"💯","name":"العلامة الكاملة","desc":"100%"},
    "5_quizzes": {"icon":"🔥","name":"مجتهد","desc":"5 اختبارات"},
    "10_quizzes": {"icon":"💪","name":"مثابر","desc":"10 اختبارات"},
    "25_quizzes": {"icon":"🏃","name":"عدّاء","desc":"25 اختبار"},
    "50_quizzes": {"icon":"🚀","name":"صاروخ","desc":"50 اختبار"},
    "100_quizzes": {"icon":"🌟","name":"أسطورة","desc":"100 اختبار"},
    "level_5": {"icon":"⭐","name":"نجم","desc":"المستوى 5"},
    "level_10": {"icon":"🌟","name":"نجم لامع","desc":"المستوى 10"},
    "level_20": {"icon":"👑","name":"ملك","desc":"المستوى 20"},
    "level_50": {"icon":"🏆","name":"أسطورة حية","desc":"المستوى 50"},
    "all_subjects": {"icon":"🎓","name":"الموسوعي","desc":"كل المواد"},
    "streak_7": {"icon":"🔥","name":"أسبوع كامل","desc":"7 أيام"},
    "streak_30": {"icon":"🌋","name":"شهر كامل","desc":"30 يوم"},
}

def check_badges(u):
    try:
        s = get_user_stats(u)
        if not s: return
        cur = set(filter(None, (s.get("badges") or "").split(",")))
        new = set()
        if s["quizzes_taken"] >= 1: new.add("first_quiz")
        if s["perfect_scores"] >= 1: new.add("perfect")
        if s["quizzes_taken"] >= 5: new.add("5_quizzes")
        if s["quizzes_taken"] >= 10: new.add("10_quizzes")
        if s["quizzes_taken"] >= 25: new.add("25_quizzes")
        if s["quizzes_taken"] >= 50: new.add("50_quizzes")
        if s["quizzes_taken"] >= 100: new.add("100_quizzes")
        if s["level"] >= 5: new.add("level_5")
        if s["level"] >= 10: new.add("level_10")
        if s["level"] >= 20: new.add("level_20")
        if s["level"] >= 50: new.add("level_50")
        if len(set(filter(None, (s.get("unique_subjects") or "").split(",")))) >= len(SUBJECTS):
            new.add("all_subjects")
        if s.get("streak", 0) >= 7: new.add("streak_7")
        if s.get("streak", 0) >= 30: new.add("streak_30")
        all_b = cur | new
        if all_b != cur:
            conn = get_db(); c = conn.cursor()
            c.execute("UPDATE user_stats SET badges=? WHERE username=?", (",".join(all_b), u))
            conn.commit(); conn.close()
            for b in (new - cur):
                if b in BADGES:
                    add_notification(u, "🏆 إنجاز", f"{BADGES[b]['icon']} {BADGES[b]['name']}", "🏆")
    except Exception: pass

def get_user_badges(u):
    s = get_user_stats(u)
    b = set(filter(None, (s.get("badges") or "").split(",")))
    return [BADGES[x] for x in b if x in BADGES]

def add_notification(u, title, msg, icon="🔔"):
    try:
        conn = get_db(); c = conn.cursor()
        c.execute("INSERT INTO notifications (username, title, message, icon) VALUES (?,?,?,?)",
                  (u, title, msg, icon))
        conn.commit(); conn.close()
    except Exception: pass

def get_notifications(u, unread=False):
    try:
        conn = get_db(); c = conn.cursor()
        if unread:
            c.execute("SELECT * FROM notifications WHERE username=? AND is_read=0 ORDER BY created_at DESC LIMIT 20", (u,))
        else:
            c.execute("SELECT * FROM notifications WHERE username=? ORDER BY created_at DESC LIMIT 20", (u,))
        rows = [dict(r) for r in c.fetchall()]; conn.close()
        return rows
    except Exception: return []

def mark_notifications_read(u):
    try:
        conn = get_db(); c = conn.cursor()
        c.execute("UPDATE notifications SET is_read=1 WHERE username=?", (u,))
        conn.commit(); conn.close()
    except Exception: pass

def check_daily_bonus(u):
    try:
        conn = get_db(); c = conn.cursor()
        c.execute("SELECT last_daily, streak FROM user_stats WHERE username=?", (u,))
        row = c.fetchone()
        if not row: conn.close(); return 0
        today = datetime.now().strftime("%Y-%m-%d")
        last = row["last_daily"]; streak = row["streak"] or 0
        if last == today: conn.close(); return 0
        yest = (datetime.now() - timedelta(days=1)).strftime("%Y-%m-%d")
        streak = streak + 1 if last == yest else 1
        bonus = min(10 + (streak - 1) * 5, 50)
        c.execute("UPDATE user_stats SET last_daily=?, streak=?, total_points=total_points+? WHERE username=?",
                  (today, streak, bonus, u))
        conn.commit(); conn.close()
        add_notification(u, "🎁 مكافأة", f"+{bonus} نقطة (Streak: {streak})", "🎁")
        return bonus
    except Exception: return 0

RANKS = [(1,"🌱 مبتدئ"),(3,"📖 متعلّم"),(5,"🎯 مجتهد"),(8,"⭐ متميز"),
         (12,"🏅 متفوق"),(20,"👑 خبير"),(35,"🏆 أسطورة"),(50,"🌟 أسطورة حية")]

def get_rank(lvl):
    r = RANKS[0][1]
    for l, n in RANKS:
        if lvl >= l: r = n
    return r

def toggle_favorite(u, lid):
    try:
        conn = get_db(); c = conn.cursor()
        c.execute("SELECT id FROM favorites WHERE username=? AND lesson_id=?", (u, lid))
        if c.fetchone():
            c.execute("DELETE FROM favorites WHERE username=? AND lesson_id=?", (u, lid))
            r = False
        else:
            c.execute("INSERT INTO favorites (username, lesson_id) VALUES (?,?)", (u, lid)); r = True
        conn.commit(); conn.close(); return r
    except Exception: return False

def is_favorite(u, lid):
    try:
        conn = get_db(); c = conn.cursor()
        c.execute("SELECT id FROM favorites WHERE username=? AND lesson_id=?", (u, lid))
        r = c.fetchone() is not None; conn.close(); return r
    except Exception: return False

def get_favorites(u):
    try:
        conn = get_db(); c = conn.cursor()
        c.execute("""SELECT l.* FROM lessons l INNER JOIN favorites f ON l.id=f.lesson_id
                     WHERE f.username=? ORDER BY f.created_at DESC""", (u,))
        rows = [dict(r) for r in c.fetchall()]; conn.close(); return rows
    except Exception: return []

def load_lessons(subject=None, language=None, owner=None, search=None):
    try:
        conn = get_db(); c = conn.cursor()
        q = "SELECT * FROM lessons WHERE 1=1"; p = []
        if subject: q += " AND subject=?"; p.append(subject)
        if language: q += " AND language=?"; p.append(language)
        if owner is not None: q += " AND owner=?"; p.append(owner)
        if search: q += " AND (title LIKE ? OR content LIKE ?)"; p += [f"%{search}%", f"%{search}%"]
        q += " ORDER BY created_at DESC"
        c.execute(q, p)
        rows = [dict(r) for r in c.fetchall()]; conn.close(); return rows
    except Exception: return []

def add_lesson(s, l, t, ct, im=None, pdf=None, ow="public"):
    try:
        conn = get_db(); c = conn.cursor()
        c.execute("INSERT INTO lessons (subject, language, title, content, image_url, pdf_url, owner) VALUES (?,?,?,?,?,?,?)",
                  (s, l, t, ct, im, pdf, ow))
        conn.commit(); conn.close(); return True, "✅"
    except Exception as e: return False, f"❌ {e}"

def delete_lesson(lid, of=None):
    try:
        conn = get_db(); c = conn.cursor()
        if of: c.execute("DELETE FROM lessons WHERE id=? AND owner=?", (lid, of))
        else: c.execute("DELETE FROM lessons WHERE id=?", (lid,))
        conn.commit(); conn.close(); return True
    except Exception: return False

def load_questions(lid):
    try:
        conn = get_db(); c = conn.cursor()
        c.execute("SELECT * FROM questions WHERE lesson_id=?", (str(lid),))
        rows = c.fetchall(); conn.close()
        return [{"id": q["id"], "question": q["question"],
                 "options": [q["option_a"], q["option_b"], q["option_c"], q["option_d"]],
                 "correct": ord(q["correct_answer"]) - 65,
                 "explanation": q["explanation"] or ""} for q in rows]
    except Exception: return []

def add_question(lid, q, a, b, cc, d, cor, exp=""):
    try:
        conn = get_db(); c = conn.cursor()
        c.execute("""INSERT INTO questions (lesson_id, question, option_a, option_b, option_c, option_d, correct_answer, explanation)
                     VALUES (?,?,?,?,?,?,?,?)""", (str(lid), q, a, b, cc, d, cor, exp))
        conn.commit(); conn.close(); return True, "✅"
    except Exception as e: return False, f"❌ {e}"

def delete_question(qid):
    try:
        conn = get_db(); c = conn.cursor()
        c.execute("DELETE FROM questions WHERE id=?", (qid,))
        conn.commit(); conn.close(); return True
    except Exception: return False

def upload_file(f, folder="uploads"):
    if f is None: return None
    try:
        fp = UPLOAD_DIR / folder; fp.mkdir(parents=True, exist_ok=True)
        ts = int(datetime.now().timestamp() * 1000)
        sn = "".join(c for c in f.name if c.isalnum() or c in "._-")
        filepath = fp / f"{ts}_{sn}"
        with open(filepath, "wb") as fh: fh.write(f.getbuffer())
        return str(filepath)
    except Exception: return None

def render_pdf(pp):
    try:
        if not os.path.exists(pp): st.error("❌ الملف ما كاينش"); return
        with open(pp, "rb") as f: b64 = base64.b64encode(f.read()).decode('utf-8')
        st.markdown(f'<iframe src="data:application/pdf;base64,{b64}" width="100%" height="600" type="application/pdf"></iframe>', unsafe_allow_html=True)
    except Exception as e: st.error(f"خطأ: {e}")

def add_review(lid, u, r, cm=""):
    try:
        conn = get_db(); c = conn.cursor()
        c.execute("INSERT OR REPLACE INTO reviews (lesson_id, username, rating, comment) VALUES (?,?,?,?)", (lid, u, r, cm))
        conn.commit(); conn.close(); return True
    except Exception: return False

def get_reviews(lid):
    try:
        conn = get_db(); c = conn.cursor()
        c.execute("SELECT * FROM reviews WHERE lesson_id=? ORDER BY created_at DESC", (lid,))
        rows = [dict(r) for r in c.fetchall()]; conn.close(); return rows
    except Exception: return []

def get_avg_rating(lid):
    try:
        conn = get_db(); c = conn.cursor()
        c.execute("SELECT AVG(rating) as avg, COUNT(*) as count FROM reviews WHERE lesson_id=?", (lid,))
        row = c.fetchone(); conn.close()
        return (row["avg"] or 0, row["count"] or 0)
    except Exception: return (0, 0)

def add_message(lid, u, m):
    try:
        conn = get_db(); c = conn.cursor()
        c.execute("INSERT INTO messages (lesson_id, username, message) VALUES (?,?,?)", (lid, u, m))
        conn.commit(); conn.close(); return True
    except Exception: return False

def get_messages(lid, limit=50):
    try:
        conn = get_db(); c = conn.cursor()
        c.execute("SELECT * FROM messages WHERE lesson_id=? ORDER BY created_at ASC LIMIT ?", (lid, limit))
        rows = [dict(r) for r in c.fetchall()]; conn.close(); return rows
    except Exception: return []

def add_flashcard(u, s, fr, bk):
    try:
        conn = get_db(); c = conn.cursor()
        c.execute("INSERT INTO flashcards (username, subject, front, back) VALUES (?,?,?,?)", (u, s, fr, bk))
        conn.commit(); conn.close(); return True
    except Exception: return False

def get_flashcards(u, s=None):
    try:
        conn = get_db(); c = conn.cursor()
        if s: c.execute("SELECT * FROM flashcards WHERE username=? AND subject=? ORDER BY created_at DESC", (u, s))
        else: c.execute("SELECT * FROM flashcards WHERE username=? ORDER BY created_at DESC", (u,))
        rows = [dict(r) for r in c.fetchall()]; conn.close(); return rows
    except Exception: return []

def delete_flashcard(fid):
    try:
        conn = get_db(); c = conn.cursor()
        c.execute("DELETE FROM flashcards WHERE id=?", (fid,))
        conn.commit(); conn.close(); return True
    except Exception: return False

def toggle_flashcard_known(fid):
    try:
        conn = get_db(); c = conn.cursor()
        c.execute("UPDATE flashcards SET known=1-known WHERE id=?", (fid,))
        conn.commit(); conn.close()
    except Exception: pass

def add_note(u, lid, n):
    try:
        conn = get_db(); c = conn.cursor()
        c.execute("INSERT INTO notes (username, lesson_id, note) VALUES (?,?,?)", (u, lid, n))
        conn.commit(); conn.close(); return True
    except Exception: return False

def get_notes(u, lid=None):
    try:
        conn = get_db(); c = conn.cursor()
        if lid: c.execute("SELECT * FROM notes WHERE username=? AND lesson_id=? ORDER BY created_at DESC", (u, lid))
        else: c.execute("SELECT * FROM notes WHERE username=? ORDER BY created_at DESC", (u,))
        rows = [dict(r) for r in c.fetchall()]; conn.close(); return rows
    except Exception: return []

def delete_note(nid):
    try:
        conn = get_db(); c = conn.cursor()
        c.execute("DELETE FROM notes WHERE id=?", (nid,))
        conn.commit(); conn.close(); return True
    except Exception: return False

def add_friend(u, fu):
    if u == fu: return False, "❌ ما تقدرش تضيف نفسك"
    try:
        conn = get_db(); c = conn.cursor()
        c.execute("SELECT username FROM users WHERE username=?", (fu,))
        if not c.fetchone(): conn.close(); return False, "❌ المستخدم ما كاينش"
        c.execute("INSERT OR IGNORE INTO friends (username, friend_username) VALUES (?,?)", (u, fu))
        c.execute("INSERT OR IGNORE INTO friends (username, friend_username) VALUES (?,?)", (fu, u))
        conn.commit(); conn.close()
        add_notification(fu, "👥 صديق جديد", f"{u} أضافك", "👥")
        return True, "✅ تم"
    except Exception as e: return False, f"❌ {e}"

def get_friends(u):
    try:
        conn = get_db(); c = conn.cursor()
        c.execute("""SELECT f.friend_username, us.full_name, s.total_points, s.level
                     FROM friends f LEFT JOIN users us ON f.friend_username=us.username
                     LEFT JOIN user_stats s ON f.friend_username=s.username
                     WHERE f.username=? ORDER BY s.total_points DESC""", (u,))
        rows = [dict(r) for r in c.fetchall()]; conn.close(); return rows
    except Exception: return []

def remove_friend(u, fu):
    try:
        conn = get_db(); c = conn.cursor()
        c.execute("DELETE FROM friends WHERE username=? AND friend_username=?", (u, fu))
        c.execute("DELETE FROM friends WHERE username=? AND friend_username=?", (fu, u))
        conn.commit(); conn.close(); return True
    except Exception: return False

def create_challenge(ch, op, lid):
    try:
        conn = get_db(); c = conn.cursor()
        c.execute("INSERT INTO challenges (challenger, opponent, lesson_id) VALUES (?,?,?)", (ch, op, str(lid)))
        conn.commit(); conn.close()
        add_notification(op, "⚔️ تحدٍ", f"{ch} تحدّاك!", "⚔️")
        return True
    except Exception: return False

def get_challenges(u):
    try:
        conn = get_db(); c = conn.cursor()
        c.execute("""SELECT * FROM challenges WHERE (challenger=? OR opponent=?) AND status!='done'
                     ORDER BY created_at DESC""", (u, u))
        rows = [dict(r) for r in c.fetchall()]; conn.close(); return rows
    except Exception: return []

def add_study_plan(u, s, p, d):
    try:
        conn = get_db(); c = conn.cursor()
        c.execute("INSERT INTO study_plan (username, subject, priority, target_date) VALUES (?,?,?,?)", (u, s, p, d))
        conn.commit(); conn.close(); return True
    except Exception: return False

def get_study_plan(u):
    try:
        conn = get_db(); c = conn.cursor()
        c.execute("SELECT * FROM study_plan WHERE username=? ORDER BY target_date", (u,))
        rows = [dict(r) for r in c.fetchall()]; conn.close(); return rows
    except Exception: return []

def toggle_study_plan(pid):
    try:
        conn = get_db(); c = conn.cursor()
        c.execute("UPDATE study_plan SET completed=1-completed WHERE id=?", (pid,))
        conn.commit(); conn.close()
    except Exception: pass

def auto_generate_plan(u):
    w = get_weaknesses(u)
    if not w: return False
    for x in w[:3]:
        p = "عالية" if x['avg'] < 40 else "متوسطة"
        d = (datetime.now() + timedelta(days=7)).strftime("%Y-%m-%d")
        add_study_plan(u, x['subject'], p, d)
    return True
TRANSLATIONS = {"ar": {
    "app_name": "منصة المراجعة", "dashboard": "🏠 الرئيسية",
    "lessons": "📚 الدروس", "quizzes": "📝 الاختبارات", "developer": "⚙️ المطور",
    "my_stats": "📊 إحصائياتي", "favorites": "⭐ المفضلة",
    "quick_review": "⚡ مراجعة سريعة", "leaderboard": "🏆 المتصدرون",
    "flashcards": "🃏 بطاقاتي", "notes": "📝 ملاحظاتي", "friends": "👥 أصدقائي",
    "challenges": "⚔️ التحديات", "weekly": "📅 الأسبوع",
    "study_plan": "📋 جدول المراجعة", "notifications": "🔔 الإشعارات",
    "welcome": "مرحباً", "subtitle": "منصة 3AC RevisioMaroc",
    "stats": "📊 إحصائياتك", "points": "النقاط", "level": "المستوى",
    "total_points": "مجموع النقاط", "quizzes_taken": "الاختبارات",
    "perfect_scores": "العلامات الكاملة", "streak": "أيام متتالية",
    "rank": "اللقب", "choose_subject": "اختر مادة", "start_review": "ابدأ",
    "tips": "💡 راجع ثم اختبر!", "lessons_bank": "بنك الدروس",
    "search_placeholder": "🔍 ابحث...", "add_favorite": "⭐ أضف",
    "remove_favorite": "☆ حذف", "quiz_lesson": "📝 اختبار",
    "no_lessons": "⚠️ لا توجد دروس", "smart_quizzes": "الاختبارات",
    "choose_lesson": "اختر الدرس", "start_quiz": "🚀 ابدأ",
    "questions_count": "عدد الأسئلة", "each_correct": "10 نقاط/إجابة",
    "final_score": "🎯 النتيجة", "excellent": "🏆 ممتاز!",
    "good": "👍 جيد", "needs_review": "📚 راجع",
    "correction": "✅ التصحيح", "question": "سؤال", "explanation": "تفسير",
    "retry": "🔄 إعادة", "choose_another": "🔙 آخر", "submit": "✅ تسليم",
    "select_answer": "اختر", "menu": "📌 القائمة", "theme": "🎨 الثيم",
    "language": "🌐 اللغة", "congrats": "🎉 مبروك!", "back": "🔙 رجوع",
    "logout": "🚪 خروج", "student_login": "🎓 تلميذ",
    "developer_login": "⚙️ مطور", "register": "📝 تسجيل",
    "guest": "👤 زائر", "username": "المستخدم", "password": "المرور",
    "full_name": "الاسم", "confirm_password": "تأكيد",
    "login_btn": "دخول", "register_btn": "تسجيل",
    "logged_as": "مسجل", "role_student": "تلميذ",
    "role_developer": "مطور", "role_guest": "زائر",
    "developer_panel": "لوحة المطور", "add_lesson": "➕ درس",
    "add_question": "➕ سؤال", "manage_lessons": "📋 الدروس",
    "manage_questions": "❓ الأسئلة", "lesson_title": "العنوان",
    "lesson_content": "المحتوى", "lesson_subject": "المادة",
    "lesson_language": "اللغة", "lesson_image": "📷 صورة",
    "lesson_pdf": "📄 PDF", "save_lesson": "💾 حفظ", "deleted": "✅ حُذف",
    "owner_public": "📚 دروس المنصة", "my_badges": "🏅 إنجازاتي",
    "no_badges": "لا إنجازات", "recent_quizzes": "📜 آخر الاختبارات",
    "subject_stats": "📊 إحصائيات المواد", "no_history": "لا سجل",
    "attempts": "المحاولات", "avg_score": "المعدل",
    "best_score": "الأفضل", "weaknesses": "📉 نقاط الضعف",
    "recommendations": "💡 توصيات", "reviews": "⭐ التقييمات",
    "your_rating": "تقييمك", "your_comment": "تعليقك",
    "submit_review": "إرسال", "no_reviews": "لا تقييمات",
    "comments": "التعليقات", "discussion": "💬 النقاش",
    "your_message": "رسالتك", "no_messages": "لا رسائل",
    "add_flashcard": "➕ بطاقة", "front": "الوجه", "back": "الظهر",
    "known": "معروفة", "unknown": "غير معروفة",
    "study_flashcards": "🃏 دراسة", "flip": "🔄 اقلب",
    "next": "➡️ التالي", "prev": "⬅️ السابق",
    "my_notes": "📝 ملاحظاتي", "add_note": "➕ ملاحظة",
    "save_note": "💾 حفظ", "no_notes": "لا ملاحظات",
    "add_friend": "➕ صديق", "friend_username": "اسم الصديق",
    "no_friends": "لا أصدقاء", "remove": "🗑️ حذف",
    "create_challenge": "⚔️ تحدٍ", "no_challenges": "لا تحديات",
    "weekly_report": "📅 تقرير الأسبوع", "lessons_completed": "الدروس",
    "points_earned": "النقاط", "study_plan_title": "📋 جدول المراجعة",
    "add_plan": "➕ إضافة", "priority": "الأولوية", "high": "عالية",
    "medium": "متوسطة", "low": "ضعيفة", "target_date": "التاريخ",
    "completed": "✅ مكتمل", "auto_generate": "🤖 توليد",
    "no_notifications": "لا إشعارات", "mark_read": "✅ قرأت الكل",
}}
for l in ["fr", "en", "es"]: TRANSLATIONS[l] = TRANSLATIONS["ar"]
LANGUAGES = {"ar": "🇲🇦 العربية"}

THEMES = {
    "⚽ FC Barcelona": {"bg":"#0A1E3F","card":"#1A2F5C","text":"#F0F8FF","accent":"#A50044","secondary":"#0F2A52","border":"#004D98","highlight":"#00D26A"},
    "👑 Real Madrid": {"bg":"#0F1B2D","card":"#1E2E4A","text":"#FFFFFF","accent":"#FEBE10","secondary":"#0A1421","border":"#00529F","highlight":"#FEBE10"},
    "🦅 الأهلي": {"bg":"#1A0A0A","card":"#2D1515","text":"#FFF5F5","accent":"#E30613","secondary":"#120505","border":"#8B0000","highlight":"#FFD700"},
    "🌙 Moonlight": {"bg":"#0A0E1A","card":"#1A1F35","text":"#E8ECFF","accent":"#7B9FFF","secondary":"#050810","border":"#3D4A7A","highlight":"#FFE57F"},
    "🌙 Midnight Purple": {"bg":"#0D0B1F","card":"#1A1735","text":"#EDE9FE","accent":"#A78BFA","secondary":"#221D4A","border":"#3D3475","highlight":"#4ADE80"},
    "🌊 Ocean Deep": {"bg":"#0A1929","card":"#132F4C","text":"#E3F2FD","accent":"#00B8D4","secondary":"#0F2537","border":"#1E4976","highlight":"#4ADE80"},
    "📚 Study Mode": {"bg":"#1A1410","card":"#2D2418","text":"#FFF8E7","accent":"#D4A574","secondary":"#0F0B07","border":"#5C4A2E","highlight":"#FFD700"},
    "🌅 Golden Sunset": {"bg":"#1F1410","card":"#331F17","text":"#FFF3E0","accent":"#FFB74D","secondary":"#2A1A12","border":"#5D3A24","highlight":"#4ADE80"},
    "🌿 Forest Emerald": {"bg":"#0B1F14","card":"#143728","text":"#E8F5E9","accent":"#4ADE80","secondary":"#0F2A1D","border":"#1E5C3D","highlight":"#00D26A"},
    "☀️ Light Mode": {"bg":"#F5F7FA","card":"#FFFFFF","text":"#1A202C","accent":"#4A90E2","secondary":"#E2E8F0","border":"#CBD5E0","highlight":"#38A169"},
    "🌌 Galaxy": {"bg":"#0D0221","card":"#1A0533","text":"#E8D5FF","accent":"#C77DFF","secondary":"#050011","border":"#7209B7","highlight":"#4CC9F0"},
}

SUBJECTS = {
    "maths": {"ar":"الرياضيات","icon":"📐","color":"#4A90E2"},
    "french": {"ar":"اللغة الفرنسية","icon":"🇫🇷","color":"#E74C3C"},
    "english": {"ar":"اللغة الإنجليزية","icon":"🇬🇧","color":"#3498DB"},
    "history": {"ar":"الاجتماعيات","icon":"🌍","color":"#F39C12"},
    "islamic": {"ar":"التربية الإسلامية","icon":"🕌","color":"#27AE60"},
    "pc": {"ar":"الفيزياء والكيمياء","icon":"⚗️","color":"#9B59B6"},
    "svt": {"ar":"علوم الحياة والأرض","icon":"🧬","color":"#16A085"},
}

def init_session_state():
    d = {"theme":"⚽ FC Barcelona","language":"ar","page":"dashboard",
         "selected_subject":None,"selected_lesson":None,"points":0,"level":1,
         "student_name":"","quiz_state":{},"quiz_finished":False,
         "current_lesson_title":"","authenticated":False,"user_role":None,
         "username":None,"full_name":None,"auth_page":"home",
         "quick_review_mode":False,"quiz_start_time":None,"quiz_time_limit":600,
         "daily_bonus_shown":False,"flashcard_index":0,"flashcard_flipped":False,
         "notifications_open":False}
    for k, v in d.items():
        if k not in st.session_state: st.session_state[k] = v

init_session_state()

def T(k): return TRANSLATIONS.get(st.session_state.language, TRANSLATIONS["ar"]).get(k, k)
def get_subject_name(k): return SUBJECTS[k].get("ar", k) if k in SUBJECTS else k

def get_progress_percent():
    s = get_user_stats(st.session_state.username)
    return s.get("total_points", 0) % 100 if s else 0

def apply_theme():
    th = THEMES[st.session_state.theme]
    hl = th.get("highlight", "#4ADE80")
    st.markdown(f"""<style>
        .stApp {{ background-color: {th['bg']}; color: {th['text']}; direction: rtl; }}
        section[data-testid="stSidebar"] {{ background-color: {th['secondary']}; border-right: 2px solid {th['accent']}; }}
        section[data-testid="stSidebar"] * {{ color: {th['text']} !important; }}
        .custom-card {{ background-color: {th['card']}; color: {th['text']}; padding: 20px;
            border-radius: 12px; border: 1px solid {th['border']}; margin-bottom: 15px;
            box-shadow: 0 4px 12px rgba(0,0,0,0.3); text-align: right; }}
        h1,h2,h3,h4,h5,h6 {{ color: {th['text']} !important; text-align: right; }}
        p,label,div {{ text-align: right; }}
        .stButton>button {{ background: linear-gradient(135deg, {th['accent']}, {th['border']});
            color: white; border-radius: 8px; border: none; padding: 10px 20px; font-weight: bold; }}
        .stTextInput input, .stSelectbox select, .stTextArea textarea {{
            background-color: {th['card']} !important; color: {th['text']} !important;
            border: 1px solid {th['border']} !important; }}
        .stProgress>div>div>div {{ background: linear-gradient(90deg, {th['accent']}, {hl}); }}
        div[data-testid="stMetricValue"] {{ color: {th['accent']} !important; }}
        .main-header {{ background: linear-gradient(135deg, {th['accent']} 0%, {th['border']} 50%, {th['accent']} 100%);
            padding: 30px; border-radius: 18px; text-align: center; margin-bottom: 25px;
            border: 2px solid {hl}; }}
        .main-header h1, .main-header p {{ color: white !important; text-align: center; }}
        .role-badge {{ display: inline-block; padding: 3px 12px; border-radius: 12px; font-size: 0.85em; font-weight: bold; }}
        .badge-card {{ background: linear-gradient(135deg, {th['accent']}, {th['border']});
            padding: 15px; border-radius: 12px; text-align: center; color: white; margin: 5px; }}
        .chat-user {{ background: {th['accent']}; color: white; padding: 10px 15px;
            border-radius: 15px; margin: 5px 0; text-align: right; }}
        .chat-other {{ background: {th['card']}; color: {th['text']}; padding: 10px 15px;
            border-radius: 15px; margin: 5px 0; border: 1px solid {th['border']}; text-align: right; }}
        .flashcard {{ background: linear-gradient(135deg, {th['card']}, {th['secondary']});
            border: 3px solid {th['accent']}; border-radius: 20px; padding: 60px 30px;
            text-align: center; min-height: 300px; display: flex; align-items: center;
            justify-content: center; font-size: 1.5em; color: {th['text']}; }}
        .footer {{ text-align: center; padding: 20px; margin-top: 40px;
            border-top: 2px solid {th['accent']}; opacity: 0.85; }}
    </style>""", unsafe_allow_html=True)
# ============================================================================
# المصادقة
# ============================================================================
def render_auth_home():
    apply_theme()
    st.markdown('<div class="main-header"><h1>🎓 3AC RevisioMaroc</h1><p>اختر طريقة الدخول</p></div>', unsafe_allow_html=True)

    c1, c2, c3 = st.columns(3)
    with c1:
        st.markdown('<div class="custom-card" style="text-align:center;"><div style="font-size:3.5em;">🎓</div><h3>دخول التلميذ</h3></div>', unsafe_allow_html=True)
        if st.button("🎓 تلميذ", use_container_width=True, key="go_student"):
            st.session_state.auth_page = "student_login"; st.rerun()
    with c2:
        st.markdown('<div class="custom-card" style="text-align:center;"><div style="font-size:3.5em;">⚙️</div><h3>دخول المطور</h3></div>', unsafe_allow_html=True)
        if st.button("⚙️ مطور", use_container_width=True, key="go_dev"):
            st.session_state.auth_page = "developer_login"; st.rerun()
    with c3:
        st.markdown('<div class="custom-card" style="text-align:center;"><div style="font-size:3.5em;">📝</div><h3>حساب جديد</h3></div>', unsafe_allow_html=True)
        if st.button("📝 تسجيل", use_container_width=True, key="go_register"):
            st.session_state.auth_page = "register"; st.rerun()

    st.markdown("---")
    c1, c2, c3 = st.columns([1, 2, 1])
    with c2:
        if st.button("👤 زائر", use_container_width=True, key="guest_btn"):
            st.session_state.authenticated = True
            st.session_state.username = "guest"
            st.session_state.user_role = "guest"
            st.session_state.full_name = "زائر"
            st.session_state.student_name = "زائر"
            st.rerun()
        st.info("💡 كزائر: تصفح بحرية")

    st.markdown('<div class="footer">© 2026 <b>Soufiane Ouhazza</b></div>', unsafe_allow_html=True)


def render_student_login():
    apply_theme()
    st.markdown('<div class="main-header"><h1>🎓 دخول التلميذ</h1></div>', unsafe_allow_html=True)
    c1, c2, c3 = st.columns([1, 2, 1])
    with c2:
        with st.form("sl_form"):
            u = st.text_input("👤 المستخدم")
            p = st.text_input("🔒 المرور", type="password")
            if st.form_submit_button("🎓 دخول", use_container_width=True):
                if not u or not p:
                    st.error("⚠️ املأ الحقول")
                else:
                    ok, user = authenticate(u, p)
                    if ok and user["role"] == "student":
                        st.session_state.authenticated = True
                        st.session_state.username = u
                        st.session_state.user_role = "student"
                        st.session_state.full_name = user["full_name"]
                        st.session_state.student_name = user["full_name"]
                        st.session_state.auth_page = "home"
                        st.rerun()
                    elif ok and user["role"] == "developer":
                        st.error("❌ حساب مطور")
                    else:
                        st.error("❌ بيانات خاطئة")
        c1, c2 = st.columns(2)
        with c1:
            if st.button("📝 تسجيل", use_container_width=True, key="sl_reg"):
                st.session_state.auth_page = "register"; st.rerun()
        with c2:
            if st.button("🔙 رجوع", use_container_width=True, key="sl_back"):
                st.session_state.auth_page = "home"; st.rerun()


def render_developer_login():
    apply_theme()
    st.markdown('<div class="main-header"><h1>⚙️ دخول المطور</h1></div>', unsafe_allow_html=True)
    c1, c2, c3 = st.columns([1, 2, 1])
    with c2:
        with st.form("dl_form"):
            u = st.text_input("👤 المستخدم")
            p = st.text_input("🔒 المرور", type="password")
            if st.form_submit_button("⚙️ دخول", use_container_width=True):
                ok, user = authenticate(u, p)
                if ok and user["role"] == "developer":
                    st.session_state.authenticated = True
                    st.session_state.username = u
                    st.session_state.user_role = "developer"
                    st.session_state.full_name = user["full_name"]
                    st.session_state.student_name = user["full_name"]
                    st.session_state.auth_page = "home"
                    st.rerun()
                else:
                    st.error("❌ بيانات خاطئة")
        if st.button("🔙 رجوع", use_container_width=True, key="dl_back"):
            st.session_state.auth_page = "home"; st.rerun()


def render_register():
    apply_theme()
    st.markdown('<div class="main-header"><h1>📝 حساب جديد</h1></div>', unsafe_allow_html=True)
    c1, c2, c3 = st.columns([1, 2, 1])
    with c2:
        with st.form("rg_form"):
            u = st.text_input("👤 المستخدم")
            n = st.text_input("📝 الاسم")
            p = st.text_input("🔒 المرور", type="password")
            p2 = st.text_input("🔒 تأكيد", type="password")
            if st.form_submit_button("📝 تسجيل", use_container_width=True):
                if not u or not p:
                    st.error("⚠️ املأ الحقول")
                elif p != p2:
                    st.error("❌ الكلمتان مختلفتان")
                else:
                    ok, msg = register_user(u, p, n)
                    if ok:
                        st.success("✅ تم! سجل الدخول")
                    else:
                        st.error(msg)
        if st.button("🔙 رجوع", use_container_width=True, key="rg_back"):
            st.session_state.auth_page = "home"; st.rerun()


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
    st.markdown(f'<div class="main-header"><h1>🎓 {T("welcome")} {name}!</h1><p>منصة المراجعة الشاملة</p></div>', unsafe_allow_html=True)

    if st.session_state.user_role == "student" and not st.session_state.get("daily_bonus_shown"):
        bonus = check_daily_bonus(username)
        if bonus > 0:
            st.success(f"🎁 مكافأة يومية: +{bonus} نقطة!")
            st.balloons()
        st.session_state.daily_bonus_shown = True

    stats = get_user_stats(username)
    tp = stats.get("total_points", 0)
    lvl = stats.get("level", 1)
    rank = get_rank(lvl)

    c1, c2, c3, c4 = st.columns(4)
    with c1: st.metric(f"🏆 {T('total_points')}", tp)
    with c2: st.metric(f"⭐ {T('level')}", f"{lvl} — {rank}")
    with c3: st.metric(f"📝 {T('quizzes_taken')}", stats.get("quizzes_taken", 0))
    with c4: st.metric(f"💯 {T('perfect_scores')}", stats.get("perfect_scores", 0))

    progress = tp % 100
    st.progress(progress / 100, text=f"التقدم: {progress}/100")

    streak = stats.get("streak", 0)
    if streak > 0:
        st.info(f"🔥 {T('streak')}: {streak} يوم")

    st.markdown("---")
    st.markdown(f"### 📖 {T('choose_subject')}")

    cols = st.columns(4)
    for idx, (key, info) in enumerate(SUBJECTS.items()):
        with cols[idx % 4]:
            st.markdown(f'<div class="custom-card" style="text-align:center; border-top: 4px solid {info["color"]};"><div style="font-size:3em;">{info["icon"]}</div><h3>{info["ar"]}</h3></div>', unsafe_allow_html=True)
            if st.button(T('start_review'), key=f"s_{key}", use_container_width=True):
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
    c1, c2 = st.columns([3, 1])
    with c1:
        search = st.text_input(T('search_placeholder'), key="search")
    with c2:
        subj_keys = ["all"] + list(SUBJECTS.keys())
        default_idx = subj_keys.index(st.session_state.selected_subject) if st.session_state.selected_subject in subj_keys else 0
        sel = st.selectbox("المادة", subj_keys, index=default_idx,
                          format_func=lambda k: "🎯 الكل" if k == "all" else f"{SUBJECTS[k]['icon']} {SUBJECTS[k]['ar']}")

    st.markdown("---")
    subj_filter = None if sel == "all" else sel
    lessons = load_lessons(subj_filter, None, owner="public", search=search or None)

    if not lessons:
        st.warning(T('no_lessons'))
        return
    for l in lessons:
        _render_lesson_card(l)


def _render_lesson_card(lesson):
    avg_r, cnt = get_avg_rating(lesson['id'])
    stars = "⭐" * int(round(avg_r)) if cnt > 0 else ""
    header = f"📖 {lesson['title']} — {get_subject_name(lesson['subject'])} {stars}"

    with st.expander(header, expanded=False):
        if st.session_state.user_role == "student":
            is_fav = is_favorite(st.session_state.username, lesson['id'])
            c1, c2 = st.columns([1, 8])
            with c1:
                if st.button("⭐" if is_fav else "☆", key=f"fav_{lesson['id']}"):
                    toggle_favorite(st.session_state.username, lesson['id'])
                    st.rerun()

        if lesson.get('content'):
            st.markdown(lesson['content'])
        if lesson.get('image_url') and os.path.exists(lesson['image_url']):
            st.image(lesson['image_url'], use_container_width=True)
        if lesson.get('pdf_url'):
            render_pdf(lesson['pdf_url'])

        st.markdown("---")

        tab1, tab2, tab3, tab4 = st.tabs(["📝 اختبار", "⭐ تقييم", "💬 نقاش", "📝 ملاحظات"])

        with tab1:
            if st.button("🚀 بدء الاختبار", key=f"q_{lesson['id']}"):
                st.session_state.selected_lesson = lesson['id']
                st.session_state.current_lesson_title = lesson['title']
                st.session_state.page = "quiz"
                st.session_state.quiz_state = {}
                st.session_state.quiz_finished = False
                st.session_state.quick_review_mode = False
                st.session_state.quiz_start_time = time.time()
                st.rerun()

        with tab2:
            _render_reviews(lesson['id'])

        with tab3:
            _render_discussion(lesson['id'])

        with tab4:
            _render_notes(lesson['id'])


def _render_reviews(lesson_id):
    if st.session_state.user_role != "student":
        st.info("التقييم للتلاميذ فقط")
    else:
        with st.form(f"rev_form_{lesson_id}"):
            r = st.slider(T('your_rating'), 1, 5, 5, key=f"r_{lesson_id}")
            cm = st.text_area(T('your_comment'), key=f"cm_{lesson_id}")
            if st.form_submit_button(T('submit_review')):
                add_review(lesson_id, st.session_state.username, r, cm)
                st.success("✅ تم")
                st.rerun()

    reviews = get_reviews(lesson_id)
    if not reviews:
        st.info(T('no_reviews'))
    else:
        avg, cnt = get_avg_rating(lesson_id)
        st.markdown(f"**{T('avg_score')}: {avg:.1f}/5 ({cnt})**")
        for r in reviews:
            st.markdown(f"**{r['username']}** — {'⭐' * r['rating']}")
            if r['comment']:
                st.caption(r['comment'])


def _render_discussion(lesson_id):
    msgs = get_messages(lesson_id)
    if not msgs:
        st.info(T('no_messages'))
    else:
        for m in msgs:
            st.markdown(f'<div class="chat-other"><b>{m["username"]}</b><br>{m["message"]}</div>', unsafe_allow_html=True)

    if st.session_state.user_role in ["student", "developer"]:
        with st.form(f"msg_form_{lesson_id}", clear_on_submit=True):
            txt = st.text_input(T('your_message'))
            if st.form_submit_button("📤"):
                if txt:
                    add_message(lesson_id, st.session_state.username, txt)
                    st.rerun()


def _render_notes(lesson_id):
    if st.session_state.user_role != "student":
        st.info("الملاحظات للتلاميذ فقط")
        return

    with st.form(f"note_form_{lesson_id}", clear_on_submit=True):
        note = st.text_area(T('add_note'), key=f"nt_{lesson_id}")
        if st.form_submit_button(T('save_note')):
            if note:
                add_note(st.session_state.username, lesson_id, note)
                st.success("✅")
                st.rerun()

    notes = get_notes(st.session_state.username, lesson_id)
    if not notes:
        st.info(T('no_notes'))
    else:
        for n in notes:
            c1, c2 = st.columns([5, 1])
            with c1:
                st.markdown(f"📝 {n['note']}")
                st.caption(n['created_at'][:16])
            with c2:
                if st.button("🗑️", key=f"dnote_{n['id']}"):
                    delete_note(n['id']); st.rerun()


# ============================================================================
# الإحصائيات
# ============================================================================
def render_my_stats():
    u = st.session_state.username
    st.markdown(f"## 📊 {T('my_stats')}")

    s = get_user_stats(u)
    lvl = s.get("level", 1)
    rank = get_rank(lvl)

    c1, c2, c3, c4 = st.columns(4)
    with c1: st.metric(f"🏆 {T('total_points')}", s.get("total_points", 0))
    with c2: st.metric(f"⭐ {T('rank')}", rank)
    with c3: st.metric(f"📝 {T('quizzes_taken')}", s.get("quizzes_taken", 0))
    with c4: st.metric(f"🔥 {T('streak')}", f"{s.get('streak', 0)} يوم")

    st.markdown("---")
    st.markdown(f"### {T('subject_stats')}")
    subj_stats = get_subject_stats(u)
    if subj_stats:
        for x in subj_stats:
            nm = get_subject_name(x['subject']) if x['subject'] in SUBJECTS else x['subject']
            ic = SUBJECTS.get(x['subject'], {}).get('icon', '📚')
            with st.expander(f"{ic} {nm}"):
                c1, c2, c3 = st.columns(3)
                with c1: st.metric(T('attempts'), x['attempts'])
                with c2: st.metric(T('avg_score'), f"{x['avg_percent']:.1f}%")
                with c3: st.metric(T('best_score'), f"{x['best_percent']:.0f}%")
    else:
        st.info(T('no_history'))

    st.markdown("---")
    st.markdown(f"### {T('weaknesses')}")
    wk = get_weaknesses(u)
    if wk:
        for x in wk:
            nm = get_subject_name(x['subject']) if x['subject'] in SUBJECTS else x['subject']
            st.warning(f"📉 **{nm}** — المعدل: {x['avg']:.0f}% — راجع!")
    else:
        st.success("✅ ما كاينش نقاط ضعف واضحة")

    st.markdown("---")
    st.markdown(f"### {T('recent_quizzes')}")
    hist = get_quiz_history(u, limit=10)
    if hist:
        for h in hist:
            ic = "🏆" if h['percent'] >= 80 else "👍" if h['percent'] >= 50 else "📚"
            st.markdown(f"{ic} **{h['lesson_title']}** — {h['score']}/{h['total']} ({h['percent']:.0f}%) — *{h['created_at'][:16]}*")
    else:
        st.info(T('no_history'))

    st.markdown("---")
    st.markdown(f"### {T('my_badges')}")
    badges = get_user_badges(u)
    if badges:
        cols = st.columns(4)
        for idx, b in enumerate(badges):
            with cols[idx % 4]:
                st.markdown(f'<div class="badge-card"><div style="font-size:2.5em;">{b["icon"]}</div><h4>{b["name"]}</h4><p style="font-size:0.85em;">{b["desc"]}</p></div>', unsafe_allow_html=True)
    else:
        st.info(T('no_badges'))


# ============================================================================
# المفضلة
# ============================================================================
def render_favorites():
    st.markdown(f"## ⭐ {T('favorites')}")
    favs = get_favorites(st.session_state.username)
    if not favs:
        st.info("لا توجد دروس فـ المفضلة")
        return
    for l in favs:
        _render_lesson_card(l)


# ============================================================================
# Leaderboard
# ============================================================================
def render_leaderboard():
    st.markdown(f"## 🏆 {T('leaderboard')}")
    period = st.radio("الفترة", ["week", "month", "all"],
                     format_func=lambda x: {"week": "📅 الأسبوع", "month": "📆 الشهر", "all": "🏆 الكل"}[x],
                     horizontal=True)
    lb = get_leaderboard(period)
    if not lb:
        st.info("لا توجد بيانات")
        return

    medals = ["🥇", "🥈", "🥉"]
    for i, row in enumerate(lb):
        medal = medals[i] if i < 3 else f"{i+1}."
        is_me = row['username'] == st.session_state.username
        prefix = "🎯 " if is_me else ""
        st.markdown(f"### {medal} {prefix}**{row['username']}**")
        c1, c2, c3 = st.columns(3)
        with c1: st.metric("النقاط", row['points'] or 0)
        with c2: st.metric("الاختبارات", row['quizzes'])
        with c3: st.metric("المعدل", f"{row['avg_percent']:.0f}%")
        st.markdown("---")


# ============================================================================
# المتابعة الأسبوعية
# ============================================================================
def render_weekly_report():
    st.markdown(f"## 📅 {T('weekly_report')}")
    u = st.session_state.username
    rep = get_weekly_report(u)
    if rep and rep.get('quizzes', 0) > 0:
        c1, c2, c3 = st.columns(3)
        with c1: st.metric("الاختبارات", rep.get('quizzes', 0))
        with c2: st.metric("المعدل", f"{rep.get('avg_percent', 0):.1f}%")
        with c3: st.metric("الإجابات الصحيحة", f"{rep.get('correct', 0)}/{rep.get('total_q', 0)}")
    else:
        st.info("ما كاينش نشاط هاد الأسبوع")

# ============================================================================
# واجهة الاختبار
# ============================================================================
def _render_quiz_ui(questions, lesson_id):
    u = st.session_state.username

    if st.session_state.quiz_start_time and not st.session_state.quiz_finished:
        elapsed = time.time() - st.session_state.quiz_start_time
        remaining = st.session_state.quiz_time_limit - elapsed
        if remaining > 0:
            m = int(remaining // 60); s = int(remaining % 60)
            st.warning(f"⏱️ الوقت المتبقي: {m:02d}:{s:02d}")
        else:
            st.error("⏰ انتهى الوقت!")
            st.session_state.quiz_finished = True

    st.markdown(f'<div class="custom-card"><h3>📝 {st.session_state.get("current_lesson_title", "")}</h3><p>عدد الأسئلة: {len(questions)} | 10 نقاط/إجابة</p></div>', unsafe_allow_html=True)

    if st.session_state.quiz_finished:
        score = st.session_state.quiz_state.get('score', 0)
        total = len(questions)
        pct = (score / total) * 100 if total > 0 else 0
        msg = T('excellent') if pct >= 80 else T('good') if pct >= 50 else T('needs_review')
        th = THEMES[st.session_state.theme]

        st.markdown(f'<div class="custom-card" style="text-align:center; border:2px solid {th["accent"]};"><h2>{T("final_score")}</h2><h1 style="font-size:3em; color:{th["accent"]};">{score} / {total}</h1><h3>{pct:.0f}%</h3><p>{msg}</p></div>', unsafe_allow_html=True)
        if pct >= 80: st.balloons()

        st.markdown(f"### {T('correction')}")
        answers = st.session_state.quiz_state.get('answers', {})
        for i, q in enumerate(questions):
            ua = answers.get(i)
            ok = ua == q['correct']
            ic = "✅" if ok else "❌"
            with st.expander(f"{ic} {T('question')} {i+1}: {q['question']}"):
                for j, opt in enumerate(q['options']):
                    mk = "🟢" if j == q['correct'] else ("🔴" if j == ua else "⚪")
                    st.markdown(f"{mk} {chr(65+j)}. {opt}")
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
            choice = st.radio(T('select_answer'), options=range(len(options)),
                              format_func=lambda j, opts=options: f"{chr(65+j)}. {opts[j]}",
                              key=f"q_{i}", index=answers.get(i, 0),
                              label_visibility="collapsed")
            answers[i] = choice
            st.markdown("---")

        if st.form_submit_button(T('submit'), use_container_width=True):
            score = sum(1 for i, q in enumerate(questions) if answers.get(i) == q['correct'])
            st.session_state.quiz_state = {'answers': answers, 'score': score}
            st.session_state.quiz_finished = True

            if st.session_state.user_role == "student":
                subj = questions[0].get('subject', 'mixed') if questions else 'mixed'
                save_quiz_result(u, lesson_id, st.session_state.current_lesson_title, subj, score, len(questions))
                update_user_stats(u, points=score * 10, quiz=True,
                                  perfect=(score == len(questions)), subject=subj)
            st.rerun()


# ============================================================================
# الاختبارات
# ============================================================================
def render_quiz():
    st.markdown(f"## 📝 {T('smart_quizzes')}")

    if not st.session_state.selected_lesson:
        all_l = load_lessons(owner="public")
        if not all_l:
            st.warning("⚠️ لا توجد دروس")
            return
        titles = {str(l['id']): f"{l['title']} ({get_subject_name(l['subject'])})" for l in all_l}
        lid = st.selectbox(T('choose_lesson'), list(titles.keys()), format_func=lambda i: titles[i])
        if st.button(T('start_quiz')):
            st.session_state.selected_lesson = lid
            st.session_state.current_lesson_title = titles[lid]
            st.session_state.quiz_state = {}
            st.session_state.quiz_finished = False
            st.session_state.quick_review_mode = False
            st.session_state.quiz_start_time = time.time()
            st.rerun()
        return

    if st.session_state.quick_review_mode:
        render_quick_review()
        return

    lid = st.session_state.selected_lesson
    questions = load_questions(lid)
    if not questions:
        st.warning("⚠️ لا توجد أسئلة")
        if st.button(T('back')):
            st.session_state.selected_lesson = None
            st.rerun()
        return
    _render_quiz_ui(questions, lid)


# ============================================================================
# المراجعة السريعة
# ============================================================================
def render_quick_review():
    st.markdown("## ⚡ مراجعة سريعة")
    st.caption("10 أسئلة عشوائية من جميع المواد")

    if not st.session_state.quick_review_mode:
        all_l = load_lessons(owner="public")
        all_q = []
        for l in all_l:
            qs = load_questions(l['id'])
            for q in qs:
                q['lesson_title'] = l['title']
                q['subject'] = l['subject']
                all_q.append(q)

        if len(all_q) < 1:
            st.warning("⚠️ ما كايناش أسئلة كافية")
            return

        st.info(f"📊 متوفر: {len(all_q)} سؤال")
        if st.button("🚀 ابدأ المراجعة", use_container_width=True):
            sample = random.sample(all_q, min(10, len(all_q)))
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
        return
    _render_quiz_ui(questions, "quick")


# ============================================================================
# Flashcards
# ============================================================================
def render_flashcards():
    st.markdown(f"## 🃏 {T('flashcards')}")
    u = st.session_state.username

    tab1, tab2 = st.tabs(["📚 دراسة", "➕ إضافة"])

    with tab2:
        with st.form("fc_form", clear_on_submit=True):
            subj = st.selectbox("المادة", list(SUBJECTS.keys()),
                                format_func=lambda k: f"{SUBJECTS[k]['icon']} {SUBJECTS[k]['ar']}",
                                key="fc_subj")
            front = st.text_area(T('front'), key="fc_front")
            back = st.text_area(T('back'), key="fc_back")
            if st.form_submit_button(T('add_flashcard')):
                if front and back:
                    add_flashcard(u, subj, front, back)
                    st.success("✅")
                    st.rerun()
                else:
                    st.error("⚠️ املأ الوجه والظهر")

    with tab1:
        cards = get_flashcards(u)
        if not cards:
            st.info("لا توجد بطاقات — أضف من التبويب الثاني")
            return

        c1, c2 = st.columns([1, 1])
        with c1:
            subj_filter = st.selectbox("فلترة", ["all"] + list(SUBJECTS.keys()),
                                       format_func=lambda k: "الكل" if k == "all" else SUBJECTS[k]['ar'],
                                       key="fc_filter")
        if subj_filter != "all":
            cards = [c for c in cards if c['subject'] == subj_filter]

        if not cards:
            st.info("لا توجد بطاقات فـ هاد المادة")
            return

        idx = st.session_state.flashcard_index % len(cards)
        card = cards[idx]

        st.markdown(f"**{idx+1} / {len(cards)}** — {'✅ معروفة' if card['known'] else '⏳ غير معروفة'}")

        text = card['back'] if st.session_state.flashcard_flipped else card['front']
        st.markdown(f'<div class="flashcard">{text}</div>', unsafe_allow_html=True)
        st.markdown("")

        c1, c2, c3, c4 = st.columns(4)
        with c1:
            if st.button("⬅️ السابق", use_container_width=True):
                st.session_state.flashcard_index = (idx - 1) % len(cards)
                st.session_state.flashcard_flipped = False
                st.rerun()
        with c2:
            if st.button("🔄 اقلب", use_container_width=True):
                st.session_state.flashcard_flipped = not st.session_state.flashcard_flipped
                st.rerun()
        with c3:
            if st.button("➡️ التالي", use_container_width=True):
                st.session_state.flashcard_index = (idx + 1) % len(cards)
                st.session_state.flashcard_flipped = False
                st.rerun()
        with c4:
            if st.button("✅ معروفة", use_container_width=True):
                toggle_flashcard_known(card['id'])
                st.session_state.flashcard_index = (idx + 1) % len(cards)
                st.session_state.flashcard_flipped = False
                st.rerun()

        with st.expander("🗑️ حذف البطاقة"):
            if st.button(f"حذف #{card['id']}", key=f"del_fc_{card['id']}"):
                delete_flashcard(card['id'])
                st.session_state.flashcard_index = 0
                st.rerun()


# ============================================================================
# جدول المراجعة
# ============================================================================
def render_study_plan():
    st.markdown(f"## 📋 {T('study_plan_title')}")
    u = st.session_state.username

    c1, c2 = st.columns([1, 1])
    with c1:
        if st.button("🤖 توليد تلقائي من نقاط الضعف", use_container_width=True):
            if auto_generate_plan(u):
                st.success("✅ تم التوليد")
                st.rerun()
            else:
                st.warning("ما كايناش نقاط ضعف")

    st.markdown("---")
    with st.form("plan_form", clear_on_submit=True):
        subj = st.selectbox("المادة", list(SUBJECTS.keys()),
                           format_func=lambda k: f"{SUBJECTS[k]['icon']} {SUBJECTS[k]['ar']}")
        priority = st.selectbox(T('priority'), ["عالية", "متوسطة", "ضعيفة"])
        target = st.date_input(T('target_date'), datetime.now() + timedelta(days=7))
        if st.form_submit_button(T('add_plan'), use_container_width=True):
            add_study_plan(u, subj, priority, target.strftime("%Y-%m-%d"))
            st.success("✅")
            st.rerun()

    st.markdown("---")
    plans = get_study_plan(u)
    if not plans:
        st.info("لا توجد خطة")
        return

    for p in plans:
        subj_name = SUBJECTS.get(p['subject'], {}).get('ar', p['subject'])
        icon = SUBJECTS.get(p['subject'], {}).get('icon', '📚')
        status = "✅" if p['completed'] else "⏳"
        c1, c2, c3 = st.columns([5, 1, 1])
        with c1:
            st.markdown(f"{status} {icon} **{subj_name}** — أولوية: *{p['priority']}* — تاريخ: {p['target_date']}")
        with c2:
            if st.button("🔄", key=f"tp_{p['id']}"):
                toggle_study_plan(p['id'])
                st.rerun()
        with c3:
            pass


# ============================================================================
# الأصدقاء
# ============================================================================
def render_friends():
    st.markdown(f"## 👥 {T('friends')}")
    u = st.session_state.username

    with st.form("friend_form", clear_on_submit=True):
        fu = st.text_input(T('friend_username'))
        if st.form_submit_button(T('add_friend')):
            if fu:
                ok, msg = add_friend(u, fu)
                if ok:
                    st.success(msg)
                    st.rerun()
                else:
                    st.error(msg)

    st.markdown("---")
    friends = get_friends(u)
    if not friends:
        st.info(T('no_friends'))
        return

    for f in friends:
        c1, c2 = st.columns([5, 1])
        with c1:
            nm = f['full_name'] or f['friend_username']
            lvl = f['level'] or 1
            pts = f['total_points'] or 0
            st.markdown(f"**👤 {nm}** (@{f['friend_username']}) — {get_rank(lvl)} — 🏆 {pts}")
        with c2:
            if st.button("🗑️", key=f"rf_{f['friend_username']}"):
                remove_friend(u, f['friend_username'])
                st.rerun()


# ============================================================================
# التحديات
# ============================================================================
def render_challenges():
    st.markdown(f"## ⚔️ {T('challenges')}")
    u = st.session_state.username

    with st.form("ch_form"):
        friends = get_friends(u)
        if not friends:
            st.warning("أضف أصدقاء أولاً")
        else:
            op = st.selectbox("الخصم", [f['friend_username'] for f in friends])
            all_l = load_lessons(owner="public")
            titles = {str(l['id']): l['title'] for l in all_l}
            if titles:
                lid = st.selectbox("الدرس", list(titles.keys()), format_func=lambda i: titles[i])
                if st.form_submit_button(T('create_challenge')):
                    create_challenge(u, op, lid)
                    st.success("✅ تم إرسال التحدي")
                    st.rerun()
            else:
                st.warning("لا توجد دروس")

    st.markdown("---")
    chs = get_challenges(u)
    if not chs:
        st.info(T('no_challenges'))
        return

    for ch in chs:
        c1, c2 = st.columns([5, 1])
        with c1:
            status = "⏳ في الانتظار"
            st.markdown(f"⚔️ **{ch['challenger']}** vs **{ch['opponent']}** — {status}")
        with c2:
            pass


# ============================================================================
# الإشعارات
# ============================================================================
def render_notifications():
    st.markdown(f"## 🔔 {T('notifications')}")
    u = st.session_state.username

    c1, c2 = st.columns([1, 1])
    with c1:
        if st.button(T('mark_read'), use_container_width=True):
            mark_notifications_read(u)
            st.rerun()

    notifs = get_notifications(u)
    if not notifs:
        st.info(T('no_notifications'))
        return

    for n in notifs:
        status = "" if n['is_read'] else "🔵 "
        st.markdown(f"{status}{n['icon']} **{n['title']}** — {n['message']}")
        st.caption(n['created_at'][:16])
        # ============================================================================
# لوحة المطور
# ============================================================================
def render_developer_panel():
    if st.session_state.user_role != "developer":
        st.error("🔒 للمطور فقط")
        st.stop()

    st.markdown(f"## ⚙️ {T('developer_panel')}")

    conn = get_db(); c = conn.cursor()
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
    tab1, tab2, tab3 = st.tabs([T('manage_lessons'), T('manage_questions'), "👥 التلاميذ"])

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
            content = st.text_area(T('lesson_content'), height=150)
            c1, c2 = st.columns(2)
            with c1: image_file = st.file_uploader(T('lesson_image'), type=["png", "jpg", "jpeg", "webp"])
            with c2: pdf_file = st.file_uploader(T('lesson_pdf'), type=["pdf"])

            if st.form_submit_button(T('save_lesson'), use_container_width=True):
                if title and (content or image_file or pdf_file):
                    image_url = upload_file(image_file, "developer/images") if image_file else None
                    pdf_url = upload_file(pdf_file, "developer/pdfs") if pdf_file else None
                    ok, msg = add_lesson(subject, language, title, content or "", image_url, pdf_url, owner="public")
                    if ok:
                        st.success("✅ تم")
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
                    qcount = len(load_questions(lesson['id']))
                    st.markdown(f"{icons} **{lesson['title']}** — {get_subject_name(lesson['subject'])} — ❓ {qcount}")
                with c2:
                    if st.button("🗑️", key=f"del_{lesson['id']}"):
                        delete_lesson(lesson['id'], owner_filter="public")
                        st.success("✅ حُذف")
                        st.rerun()
        else:
            st.info("لا توجد دروس")

    with tab2:
        st.markdown(f"### {T('add_question')}")
        all_lessons = load_lessons(owner="public")
        lesson_options = {str(l['id']): f"[{get_subject_name(l['subject'])}] {l['title']}" for l in all_lessons}

        if not lesson_options:
            st.warning("⚠️ أضف درساً أولاً")
        else:
            with st.form("add_question_form", clear_on_submit=True):
                lesson_id = st.selectbox("الدرس", list(lesson_options.keys()),
                                         format_func=lambda i: lesson_options[i])
                q_text = st.text_area("نص السؤال")
                c1, c2 = st.columns(2)
                with c1:
                    opt_a = st.text_input("A")
                    opt_b = st.text_input("B")
                with c2:
                    opt_c = st.text_input("C")
                    opt_d = st.text_input("D")
                correct = st.radio("الإجابة الصحيحة", options=[0, 1, 2, 3],
                                   format_func=lambda i: chr(65+i), horizontal=True)
                explanation = st.text_input("التفسير (اختياري)")

                if st.form_submit_button("💾 حفظ السؤال", use_container_width=True):
                    if q_text and opt_a and opt_b and opt_c and opt_d:
                        ok, msg = add_question(lesson_id, q_text, opt_a, opt_b, opt_c, opt_d, chr(65+correct), explanation)
                        if ok:
                            st.success("✅ تم")
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
                with st.expander(f"📖 {l['title']} ({len(qs)} سؤال)"):
                    for q in qs:
                        c1, c2 = st.columns([5, 1])
                        with c1:
                            st.markdown(f"❓ {q['question']} — ✅ **{chr(65+q['correct'])}**")
                        with c2:
                            if st.button("🗑️", key=f"delq_{q['id']}"):
                                delete_question(q['id'])
                                st.rerun()

    with tab3:
        st.markdown("### 👥 قائمة التلاميذ")
        conn = get_db(); c = conn.cursor()
        c.execute("""SELECT u.username, u.full_name, u.created_at,
                            s.total_points, s.level, s.quizzes_taken
                     FROM users u LEFT JOIN user_stats s ON u.username = s.username
                     WHERE u.role='student' ORDER BY s.total_points DESC""")
        students = [dict(r) for r in c.fetchall()]
        conn.close()

        if not students:
            st.info("لا يوجد تلاميذ")
        else:
            for s in students:
                c1, c2 = st.columns([5, 1])
                with c1:
                    nm = s['full_name'] or s['username']
                    lvl = s['level'] or 1
                    pts = s['total_points'] or 0
                    qz = s['quizzes_taken'] or 0
                    st.markdown(f"👤 **{nm}** (@{s['username']}) — {get_rank(lvl)} — 🏆 {pts} — 📝 {qz}")
                with c2:
                    if st.button("🗑️", key=f"delu_{s['username']}"):
                        conn = get_db(); c = conn.cursor()
                        c.execute("DELETE FROM users WHERE username=?", (s['username'],))
                        c.execute("DELETE FROM user_stats WHERE username=?", (s['username'],))
                        c.execute("DELETE FROM quiz_history WHERE username=?", (s['username'],))
                        conn.commit(); conn.close()
                        st.success("✅ حُذف")
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
    role_label = {"student": "تلميذ", "developer": "مطور", "guest": "زائر"}.get(role, role)
    badge_color = {"student": "#3498DB", "developer": theme_colors['accent'], "guest": "#95A5A6"}.get(role, "#4A90E2")

    st.markdown(f"""
    <div class="custom-card" style="text-align:center; padding: 12px;">
        <p style="margin:0; font-size: 0.9em; opacity: 0.7;">مسجل كـ</p>
        <p style="margin:5px 0; font-weight: bold;">{st.session_state.full_name or st.session_state.username}</p>
        <span class="role-badge" style="background:{badge_color}; color:white;">{role_label}</span>
    </div>
    """, unsafe_allow_html=True)

    if role == "student":
        stats = get_user_stats(st.session_state.username)
        lvl = stats.get("level", 1)
        rank = get_rank(lvl)
        st.markdown(f"""
        <div class="custom-card" style="text-align:center; padding: 12px;">
            <p style="margin:0; font-size: 1.1em;">{rank}</p>
            <p style="margin:5px 0; opacity: 0.8;">🏆 {stats.get('total_points', 0)} نقطة</p>
        </div>
        """, unsafe_allow_html=True)

        unread = len(get_notifications(st.session_state.username, unread_only=True))
        if unread > 0:
            st.warning(f"🔔 {unread} إشعار جديد")

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

    if st.button(T('leaderboard'), use_container_width=True):
        st.session_state.page = "leaderboard"
        st.rerun()

    if role == "student":
        if st.button(T('favorites'), use_container_width=True):
            st.session_state.page = "favorites"
            st.rerun()
        if st.button(T('my_stats'), use_container_width=True):
            st.session_state.page = "my_stats"
            st.rerun()
        if st.button(T('flashcards'), use_container_width=True):
            st.session_state.page = "flashcards"
            st.rerun()
        if st.button(T('study_plan'), use_container_width=True):
            st.session_state.page = "study_plan"
            st.rerun()
        if st.button(T('friends'), use_container_width=True):
            st.session_state.page = "friends"
            st.rerun()
        if st.button(T('challenges'), use_container_width=True):
            st.session_state.page = "challenges"
            st.rerun()
        if st.button(T('weekly'), use_container_width=True):
            st.session_state.page = "weekly"
            st.rerun()
        if st.button(T('notifications'), use_container_width=True):
            st.session_state.page = "notifications"
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

if page in ["favorites", "my_stats", "flashcards", "study_plan", "friends", "challenges", "weekly", "notifications"] \
   and st.session_state.user_role != "student":
    st.error("🔒 للتلاميذ فقط")
    st.session_state.page = "dashboard"
    st.rerun()

if page == "dashboard": render_dashboard()
elif page == "lessons": render_lessons()
elif page == "quiz": render_quiz()
elif page == "quick_review": render_quick_review()
elif page == "leaderboard": render_leaderboard()
elif page == "favorites" and st.session_state.user_role == "student": render_favorites()
elif page == "my_stats" and st.session_state.user_role == "student": render_my_stats()
elif page == "flashcards" and st.session_state.user_role == "student": render_flashcards()
elif page == "study_plan" and st.session_state.user_role == "student": render_study_plan()
elif page == "friends" and st.session_state.user_role == "student": render_friends()
elif page == "challenges" and st.session_state.user_role == "student": render_challenges()
elif page == "weekly" and st.session_state.user_role == "student": render_weekly_report()
elif page == "notifications" and st.session_state.user_role == "student": render_notifications()
elif page == "developer" and st.session_state.user_role == "developer": render_developer_panel()
else: render_dashboard()

st.markdown("""
<div class="footer">
    © 2026 <b>Soufiane Ouhazza</b> — 3AC RevisioMaroc<br>All Rights Reserved
</div>
""", unsafe_allow_html=True)
