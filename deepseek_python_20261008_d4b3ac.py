# ============================================================================
# 3AC RevisioMaroc - نسخة SQLite
# © 2026 Soufiane Ouhazza - All Rights Reserved
# ============================================================================

import streamlit as st
import hashlib
import sqlite3
import os
import base64
from datetime import datetime
from pathlib import Path

# ----------------------------------------------------------------------------
# إعدادات الصفحة
# ----------------------------------------------------------------------------
st.set_page_config(
    page_title="3AC RevisioMaroc",
    page_icon="🎓",
    layout="wide",
    initial_sidebar_state="expanded"
)

# ----------------------------------------------------------------------------
# إعداد قاعدة البيانات SQLite
# ----------------------------------------------------------------------------
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

    # جدول المستخدمين
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

    # جدول الدروس
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

    # جدول الأسئلة
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

    # إنشاء حساب المطور إذا ما كانش
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
# إدارة الدروس
# ----------------------------------------------------------------------------
def load_lessons(subject=None, language=None, owner=None):
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
        c.execute(query, params)
        rows = [dict(r) for r in c.fetchall()]
        conn.close()
        return rows
    except Exception as e:
        st.error(f"❌ خطأ في جلب الدروس: {e}")
        return []

def add_lesson(subject, language, title, content, image_url=None, pdf_url=None, owner="public"):
    try:
        conn = get_db()
        c = conn.cursor()
        c.execute(
            """INSERT INTO lessons (subject, language, title, content, image_url, pdf_url, owner)
               VALUES (?, ?, ?, ?, ?, ?, ?)""",
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

# ----------------------------------------------------------------------------
# إدارة الأسئلة
# ----------------------------------------------------------------------------
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
        st.error(f"❌ خطأ في جلب الأسئلة: {e}")
        return []

def add_question(lesson_id, question, opt_a, opt_b, opt_c, opt_d, correct_letter, explanation=""):
    try:
        conn = get_db()
        c = conn.cursor()
        c.execute(
            """INSERT INTO questions 
               (lesson_id, question, option_a, option_b, option_c, option_d, correct_answer, explanation)
               VALUES (?, ?, ?, ?, ?, ?, ?, ?)""",
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

# ----------------------------------------------------------------------------
# رفع الملفات (تخزين محلي)
# ----------------------------------------------------------------------------
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
        st.error(f"❌ خطأ في رفع الملف: {e}")
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
# 🌐 الترجمات
# ----------------------------------------------------------------------------
TRANSLATIONS = {
    "ar": {
        "app_name": "منصة المراجعة الشاملة",
        "dashboard": "🏠 الرئيسية", "lessons": "📚 الدروس", "quizzes": "📝 الاختبارات",
        "my_files": "📁 ملفاتي", "developer": "⚙️ لوحة المطور",
        "welcome": "مرحباً", "subtitle": "منصة 3AC RevisioMaroc لمراجعة شاملة لجميع المواد الدراسية",
        "stats": "📊 إحصائياتك", "points": "النقاط", "level": "المستوى",
        "subjects_count": "المواد", "progress": "التقدم",
        "choose_subject": "اختر مادة للمراجعة", "start_review": "ابدأ المراجعة",
        "tips": "💡 نصيحة: راجع الدروس أولاً، ثم اختبر نفسك!",
        "lessons_bank": "بنك الملخصات والدروس",
        "choose_lesson_subject": "اختر المادة", "quiz_lesson": "📝 اختبار هذا الدرس",
        "no_lessons": "⚠️ لا توجد دروس متاحة لهذه المادة حالياً",
        "smart_quizzes": "الاختبارات الذكية", "choose_lesson": "اختر الدرس",
        "start_quiz": "🚀 بدء الاختبار", "questions_count": "عدد الأسئلة",
        "each_correct": "كل إجابة صحيحة = 10 نقاط",
        "final_score": "🎯 نتيجتك النهائية",
        "excellent": "🏆 ممتاز! أداء رائع", "good": "👍 جيد! واصل المجهود",
        "needs_review": "📚 يحتاج إلى مراجعة",
        "correction": "✅ التصحيح", "question": "السؤال", "explanation": "التفسير",
        "retry": "🔄 إعادة الاختبار", "choose_another": "🔙 اختيار درس آخر",
        "submit": "✅ تسليم الإجابات", "select_answer": "اختر الإجابة",
        "student_name": "الاسم", "student_info": "👤 معلومات التلميذ",
        "menu": "📌 القائمة", "your_progress": "🏆 تقدمك",
        "level_progress": "التقدم في المستوى",
        "theme": "🎨 اختر الثيم", "appearance": "المظهر",
        "language": "🌐 اللغة", "choose_language": "اختر لغة الواجهة",
        "congrats": "🎉 مبروك! ارتقيت إلى المستوى",
        "no_questions": "⚠️ لا توجد أسئلة متاحة", "back": "🔙 رجوع",
        "quiz_of": "اختبار:", "no_lessons_quiz": "⚠️ لا توجد دروس متاحة",
        "student_login": "🎓 دخول التلميذ",
        "developer_login": "⚙️ دخول المطور",
        "register": "📝 إنشاء حساب",
        "guest": "👤 الدخول كزائر",
        "username": "اسم المستخدم",
        "password": "كلمة المرور", "full_name": "الاسم الكامل",
        "confirm_password": "تأكيد كلمة المرور",
        "login_btn": "دخول", "register_btn": "تسجيل", "logout": "🚪 تسجيل الخروج",
        "auth_subtitle": "اختر طريقة الدخول المناسبة لك",
        "wrong_creds": "❌ اسم المستخدم أو كلمة المرور خاطئة",
        "guest_note": "💡 كزائر: يمكنك تصفح الدروس والاختبارات، لكن لن تُحفظ نتائجك.",
        "logged_as": "مسجل الدخول كـ", "role_student": "تلميذ",
        "role_developer": "مطور", "role_guest": "زائر",
        "student_login_title": "🎓 دخول التلميذ",
        "student_login_subtitle": "أدخل معلوماتك للوصول إلى الدروس والاختبارات",
        "developer_login_title": "⚙️ دخول المطور",
        "developer_login_subtitle": "هذه الصفحة مخصصة للمطور فقط",
        "register_title": "📝 إنشاء حساب جديد",
        "register_subtitle": "أنشئ حسابك للاستفادة من كل الميزات",
        "back_to_login": "🔙 رجوع",
        "register_success": "✅ تم إنشاء الحساب بنجاح! يمكنك الآن تسجيل الدخول",
        "name_required": "⚠️ يرجى ملء جميع الحقول",
        "password_mismatch": "❌ كلمتا المرور غير متطابقتين",
        "developer_panel": "لوحة تحكم المطور",
        "add_lesson": "➕ إضافة درس جديد", "add_question": "➕ إضافة سؤال جديد",
        "manage_lessons": "📋 إدارة الدروس", "manage_questions": "❓ إدارة الأسئلة",
        "lesson_title": "عنوان الدرس", "lesson_content": "محتوى الدرس (نصي)",
        "lesson_subject": "المادة", "lesson_language": "اللغة",
        "lesson_image": "📷 رفع صورة (اختياري)",
        "lesson_pdf": "📄 رفع ملف PDF (اختياري)",
        "save_lesson": "💾 حفظ الدرس", "lesson_saved": "✅ تم حفظ الدرس بنجاح",
        "question_text": "نص السؤال", "option_a": "الخيار A",
        "option_b": "الخيار B", "option_c": "الخيار C", "option_d": "الخيار D",
        "correct_answer": "الإجابة الصحيحة", "explanation_text": "التفسير (اختياري)",
        "save_question": "💾 حفظ السؤال", "question_saved": "✅ تم حفظ السؤال بنجاح",
        "select_lesson_for_question": "اختر الدرس المرتبط بالسؤال",
        "deleted": "✅ تم الحذف",
        "no_custom_lessons": "لا توجد دروس بعد — ابدأ بإضافة درس",
        "no_custom_questions": "لا توجد أسئلة بعد",
        "lesson_content_optional": "(اتركه فارغاً إذا كنت ستستعمل صورة أو PDF فقط)",
        "lesson_content_label": "محتوى نصي (اختياري)",
        "dev_only_note": "🔒 هذه اللوحة متاحة فقط للمطور Soufiane Ouhazza",
        "owner_public": "📚 دروس المنصة",
        "owner_mine": "📁 دروسي",
    },
    "fr": {
        "app_name": "Plateforme de révision",
        "dashboard": "🏠 Accueil", "lessons": "📚 Leçons", "quizzes": "📝 Quiz",
        "my_files": "📁 Mes fichiers", "developer": "⚙️ Panneau Dev",
        "welcome": "Bienvenue", "subtitle": "3AC RevisioMaroc - Révisez toutes les matières",
        "stats": "📊 Statistiques", "points": "Points", "level": "Niveau",
        "subjects_count": "Matières", "progress": "Progrès",
        "choose_subject": "Choisissez une matière", "start_review": "Commencer",
        "tips": "💡 Révisez puis testez-vous !",
        "lessons_bank": "Banque de leçons",
        "choose_lesson_subject": "Choisir la matière", "quiz_lesson": "📝 Quiz",
        "no_lessons": "⚠️ Aucune leçon disponible",
        "smart_quizzes": "Quiz intelligents", "choose_lesson": "Choisir la leçon",
        "start_quiz": "🚀 Démarrer", "questions_count": "Nombre de questions",
        "each_correct": "Bonne réponse = 10 points",
        "final_score": "🎯 Score final",
        "excellent": "🏆 Excellent !", "good": "👍 Bien !",
        "needs_review": "📚 À revoir",
        "correction": "✅ Correction", "question": "Question", "explanation": "Explication",
        "retry": "🔄 Refaire", "choose_another": "🔙 Autre leçon",
        "submit": "✅ Soumettre", "select_answer": "Choisir",
        "student_name": "Nom", "student_info": "👤 Élève",
        "menu": "📌 Menu", "your_progress": "🏆 Progrès",
        "level_progress": "Progrès du niveau",
        "theme": "🎨 Thème", "appearance": "Apparence",
        "language": "🌐 Langue", "choose_language": "Choisir la langue",
        "congrats": "🎉 Bravo ! Niveau",
        "no_questions": "⚠️ Aucune question", "back": "🔙 Retour",
        "quiz_of": "Quiz :", "no_lessons_quiz": "⚠️ Aucune leçon",
        "student_login": "🎓 Connexion Élève",
        "developer_login": "⚙️ Connexion Dev",
        "register": "📝 Inscription",
        "guest": "👤 Invité",
        "username": "Nom d'utilisateur",
        "password": "Mot de passe", "full_name": "Nom complet",
        "confirm_password": "Confirmer mot de passe",
        "login_btn": "Connexion", "register_btn": "S'inscrire", "logout": "🚪 Déconnexion",
        "auth_subtitle": "Choisissez votre mode de connexion",
        "wrong_creds": "❌ Identifiants incorrects",
        "guest_note": "💡 Invité : naviguez librement, résultats non sauvegardés.",
        "logged_as": "Connecté en tant que", "role_student": "Élève",
        "role_developer": "Développeur", "role_guest": "Invité",
        "student_login_title": "🎓 Connexion Élève",
        "student_login_subtitle": "Entrez vos informations",
        "developer_login_title": "⚙️ Connexion Développeur",
        "developer_login_subtitle": "Cette page est réservée au développeur",
        "register_title": "📝 Créer un compte",
        "register_subtitle": "Créez votre compte",
        "back_to_login": "🔙 Retour",
        "register_success": "✅ Compte créé ! Connectez-vous",
        "name_required": "⚠️ Remplissez tous les champs",
        "password_mismatch": "❌ Mots de passe différents",
        "developer_panel": "Panneau développeur",
        "add_lesson": "➕ Ajouter leçon", "add_question": "➕ Ajouter question",
        "manage_lessons": "📋 Gérer leçons", "manage_questions": "❓ Gérer questions",
        "lesson_title": "Titre", "lesson_content": "Contenu (texte)",
        "lesson_subject": "Matière", "lesson_language": "Langue",
        "lesson_image": "📷 Image (optionnel)",
        "lesson_pdf": "📄 PDF (optionnel)",
        "save_lesson": "💾 Sauvegarder", "lesson_saved": "✅ Leçon sauvegardée",
        "question_text": "Question", "option_a": "Option A",
        "option_b": "Option B", "option_c": "Option C", "option_d": "Option D",
        "correct_answer": "Réponse correcte", "explanation_text": "Explication (optionnel)",
        "save_question": "💾 Sauvegarder", "question_saved": "✅ Question sauvegardée",
        "select_lesson_for_question": "Choisir la leçon",
        "deleted": "✅ Supprimé",
        "no_custom_lessons": "Aucune leçon — commencez par en ajouter",
        "no_custom_questions": "Aucune question",
        "lesson_content_optional": "(Laissez vide si vous utilisez une image/PDF)",
        "lesson_content_label": "Contenu texte (optionnel)",
        "dev_only_note": "🔒 Panneau réservé au développeur Soufiane Ouhazza",
        "owner_public": "📚 Leçons de la plateforme",
        "owner_mine": "📁 Mes leçons",
    },
    "en": {
        "app_name": "Revision Platform",
        "dashboard": "🏠 Home", "lessons": "📚 Lessons", "quizzes": "📝 Quizzes",
        "my_files": "📁 My Files", "developer": "⚙️ Dev Panel",
        "welcome": "Welcome", "subtitle": "3AC RevisioMaroc - Revise all subjects",
        "stats": "📊 Your Stats", "points": "Points", "level": "Level",
        "subjects_count": "Subjects", "progress": "Progress",
        "choose_subject": "Choose a subject", "start_review": "Start",
        "tips": "💡 Review then test yourself!",
        "lessons_bank": "Lessons Bank",
        "choose_lesson_subject": "Choose subject", "quiz_lesson": "📝 Quiz",
        "no_lessons": "⚠️ No lessons available",
        "smart_quizzes": "Smart Quizzes", "choose_lesson": "Choose lesson",
        "start_quiz": "🚀 Start", "questions_count": "Questions",
        "each_correct": "Correct = 10 points",
        "final_score": "🎯 Final Score",
        "excellent": "🏆 Excellent!", "good": "👍 Good!",
        "needs_review": "📚 Needs review",
        "correction": "✅ Correction", "question": "Question", "explanation": "Explanation",
        "retry": "🔄 Retry", "choose_another": "🔙 Another lesson",
        "submit": "✅ Submit", "select_answer": "Select",
        "student_name": "Name", "student_info": "👤 Student",
        "menu": "📌 Menu", "your_progress": "🏆 Progress",
        "level_progress": "Level progress",
        "theme": "🎨 Theme", "appearance": "Appearance",
        "language": "🌐 Language", "choose_language": "Choose language",
        "congrats": "🎉 Congrats! Level",
        "no_questions": "⚠️ No questions", "back": "🔙 Back",
        "quiz_of": "Quiz:", "no_lessons_quiz": "⚠️ No lessons",
        "student_login": "🎓 Student Login",
        "developer_login": "⚙️ Developer Login",
        "register": "📝 Register",
        "guest": "👤 Guest",
        "username": "Username",
        "password": "Password", "full_name": "Full name",
        "confirm_password": "Confirm password",
        "login_btn": "Login", "register_btn": "Register", "logout": "🚪 Logout",
        "auth_subtitle": "Choose your login method",
        "wrong_creds": "❌ Wrong credentials",
        "guest_note": "💡 Guest: browse freely, results not saved.",
        "logged_as": "Logged in as", "role_student": "Student",
        "role_developer": "Developer", "role_guest": "Guest",
        "student_login_title": "🎓 Student Login",
        "student_login_subtitle": "Enter your info",
        "developer_login_title": "⚙️ Developer Login",
        "developer_login_subtitle": "This page is for the developer only",
        "register_title": "📝 Create Account",
        "register_subtitle": "Create your account",
        "back_to_login": "🔙 Back",
        "register_success": "✅ Account created! Login now",
        "name_required": "⚠️ Fill all fields",
        "password_mismatch": "❌ Passwords don't match",
        "developer_panel": "Developer Panel",
        "add_lesson": "➕ Add Lesson", "add_question": "➕ Add Question",
        "manage_lessons": "📋 Manage Lessons", "manage_questions": "❓ Manage Questions",
        "lesson_title": "Title", "lesson_content": "Content (text)",
        "lesson_subject": "Subject", "lesson_language": "Language",
        "lesson_image": "📷 Image (optional)",
        "lesson_pdf": "📄 PDF (optional)",
        "save_lesson": "💾 Save Lesson", "lesson_saved": "✅ Lesson saved",
        "question_text": "Question", "option_a": "Option A",
        "option_b": "Option B", "option_c": "Option C", "option_d": "Option D",
        "correct_answer": "Correct Answer", "explanation_text": "Explanation (optional)",
        "save_question": "💾 Save Question", "question_saved": "✅ Question saved",
        "select_lesson_for_question": "Select lesson",
        "deleted": "✅ Deleted",
        "no_custom_lessons": "No lessons — start by adding",
        "no_custom_questions": "No questions",
        "lesson_content_optional": "(Leave empty if using image/PDF only)",
        "lesson_content_label": "Text content (optional)",
        "dev_only_note": "🔒 Developer panel - reserved to Soufiane Ouhazza",
        "owner_public": "📚 Platform Lessons",
        "owner_mine": "📁 My Lessons",
    },
    "es": {
        "app_name": "Plataforma de revisión",
        "dashboard": "🏠 Inicio", "lessons": "📚 Lecciones", "quizzes": "📝 Cuestionarios",
        "my_files": "📁 Mis archivos", "developer": "⚙️ Panel Dev",
        "welcome": "Bienvenido", "subtitle": "3AC RevisioMaroc - Revisa todas las materias",
        "stats": "📊 Estadísticas", "points": "Puntos", "level": "Nivel",
        "subjects_count": "Materias", "progress": "Progreso",
        "choose_subject": "Elige materia", "start_review": "Comenzar",
        "tips": "💡 ¡Revisa y pruébate!",
        "lessons_bank": "Banco de lecciones",
        "choose_lesson_subject": "Elegir materia", "quiz_lesson": "📝 Cuestionario",
        "no_lessons": "⚠️ No hay lecciones",
        "smart_quizzes": "Cuestionarios", "choose_lesson": "Elegir lección",
        "start_quiz": "🚀 Iniciar", "questions_count": "Preguntas",
        "each_correct": "Correcta = 10 puntos",
        "final_score": "🎯 Puntuación",
        "excellent": "🏆 ¡Excelente!", "good": "👍 ¡Bien!",
        "needs_review": "📚 Necesita repaso",
        "correction": "✅ Corrección", "question": "Pregunta", "explanation": "Explicación",
        "retry": "🔄 Reintentar", "choose_another": "🔙 Otra lección",
        "submit": "✅ Enviar", "select_answer": "Elegir",
        "student_name": "Nombre", "student_info": "👤 Estudiante",
        "menu": "📌 Menú", "your_progress": "🏆 Progreso",
        "level_progress": "Progreso del nivel",
        "theme": "🎨 Tema", "appearance": "Apariencia",
        "language": "🌐 Idioma", "choose_language": "Elegir idioma",
        "congrats": "🎉 ¡Felicidades! Nivel",
        "no_questions": "⚠️ No hay preguntas", "back": "🔙 Volver",
        "quiz_of": "Cuestionario:", "no_lessons_quiz": "⚠️ No hay lecciones",
        "student_login": "🎓 Estudiante",
        "developer_login": "⚙️ Desarrollador",
        "register": "📝 Registrarse",
        "guest": "👤 Invitado",
        "username": "Usuario",
        "password": "Contraseña", "full_name": "Nombre completo",
        "confirm_password": "Confirmar contraseña",
        "login_btn": "Entrar", "register_btn": "Registrar", "logout": "🚪 Salir",
        "auth_subtitle": "Elige tu modo de acceso",
        "wrong_creds": "❌ Credenciales incorrectas",
        "guest_note": "💡 Invitado: navega libremente",
        "logged_as": "Sesión de", "role_student": "Estudiante",
        "role_developer": "Desarrollador", "role_guest": "Invitado",
        "student_login_title": "🎓 Acceso Estudiante",
        "student_login_subtitle": "Introduce tus datos",
        "developer_login_title": "⚙️ Acceso Desarrollador",
        "developer_login_subtitle": "Solo para el desarrollador",
        "register_title": "📝 Crear Cuenta",
        "register_subtitle": "Crea tu cuenta",
        "back_to_login": "🔙 Volver",
        "register_success": "✅ ¡Cuenta creada! Ya puedes entrar",
        "name_required": "⚠️ Rellena todos los campos",
        "password_mismatch": "❌ Las contraseñas no coinciden",
        "developer_panel": "Panel del desarrollador",
        "add_lesson": "➕ Añadir lección", "add_question": "➕ Añadir pregunta",
        "manage_lessons": "📋 Gestionar lecciones", "manage_questions": "❓ Gestionar preguntas",
        "lesson_title": "Título", "lesson_content": "Contenido (texto)",
        "lesson_subject": "Materia", "lesson_language": "Idioma",
        "lesson_image": "📷 Imagen (opcional)",
        "lesson_pdf": "📄 PDF (opcional)",
        "save_lesson": "💾 Guardar", "lesson_saved": "✅ Lección guardada",
        "question_text": "Pregunta", "option_a": "Opción A",
        "option_b": "Opción B", "option_c": "Opción C", "option_d": "Opción D",
        "correct_answer": "Respuesta correcta", "explanation_text": "Explicación (opcional)",
        "save_question": "💾 Guardar", "question_saved": "✅ Pregunta guardada",
        "select_lesson_for_question": "Elegir lección",
        "deleted": "✅ Eliminado",
        "no_custom_lessons": "Sin lecciones — empieza añadiendo",
        "no_custom_questions": "Sin preguntas",
        "lesson_content_optional": "(Deja vacío si usas imagen/PDF)",
        "lesson_content_label": "Contenido de texto (opcional)",
        "dev_only_note": "🔒 Panel exclusivo del desarrollador Soufiane Ouhazza",
        "owner_public": "📚 Lecciones de la plataforma",
        "owner_mine": "📁 Mis lecciones",
    },
}

LANGUAGES = {
    "ar": "🇲🇦 العربية",
    "fr": "🇫🇷 Français",
    "en": "🇬🇧 English",
    "es": "🇪🇸 Español",
}

# ----------------------------------------------------------------------------
# 🎨 الثيمات (9 ثيمات)
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
    "🦅 الأهلي المصري": {
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
}

# ----------------------------------------------------------------------------
# المواد الدراسية
# ----------------------------------------------------------------------------
SUBJECTS = {
    "maths":   {"ar": "الرياضيات",         "fr": "Mathématiques",  "en": "Mathematics",    "es": "Matemáticas",  "icon": "📐", "color": "#4A90E2"},
    "french":  {"ar": "اللغة الفرنسية",     "fr": "Français",       "en": "French",         "es": "Francés",      "icon": "🇫🇷", "color": "#E74C3C"},
    "english": {"ar": "اللغة الإنجليزية",   "fr": "Anglais",        "en": "English",        "es": "Inglés",       "icon": "🇬🇧", "color": "#3498DB"},
    "history": {"ar": "الاجتماعيات",        "fr": "Histoire-Géo",   "en": "History & Geo",  "es": "Historia",     "icon": "🌍", "color": "#F39C12"},
    "islamic": {"ar": "التربية الإسلامية",  "fr": "Éducation Islamique", "en": "Islamic Education", "es": "Educación Islámica", "icon": "🕌", "color": "#27AE60"},
    "pc":      {"ar": "الفيزياء والكيمياء", "fr": "Physique-Chimie", "en": "Physics & Chem", "es": "Física y Química", "icon": "⚗️", "color": "#9B59B6"},
    "svt":     {"ar": "علوم الحياة والأرض", "fr": "SVT",            "en": "Life & Earth",   "es": "Biología",     "icon": "🧬", "color": "#16A085"},
}

# ----------------------------------------------------------------------------
# إدارة الجلسة
# ----------------------------------------------------------------------------
def init_session_state():
    defaults = {
        "theme": "⚽ FC Barcelona",
        "language": "ar", "page": "dashboard",
        "selected_subject": None, "selected_lesson": None,
        "points": 0, "level": 1, "student_name": "",
        "quiz_state": {}, "quiz_finished": False, "current_lesson_title": "",
        "authenticated": False, "user_role": None, "username": None, "full_name": None,
        "auth_page": "home",
    }
    for k, v in defaults.items():
        if k not in st.session_state:
            st.session_state[k] = v

init_session_state()

# ----------------------------------------------------------------------------
# دوال مساعدة
# ----------------------------------------------------------------------------
def T(key):
    lang = st.session_state.language
    return TRANSLATIONS.get(lang, TRANSLATIONS["ar"]).get(key, key)

def get_subject_name(subject_key):
    lang = st.session_state.language
    return SUBJECTS[subject_key].get(lang, SUBJECTS[subject_key]["ar"])

def add_points(points):
    st.session_state.points += points
    new_level = st.session_state.points // 100 + 1
    if new_level > st.session_state.level:
        st.session_state.level = new_level
        st.balloons()
        st.success(f"{T('congrats')} {new_level}!")

def get_progress_percent():
    return st.session_state.points % 100

# ----------------------------------------------------------------------------
# تطبيق الثيم
# ----------------------------------------------------------------------------
def apply_theme():
    theme = THEMES[st.session_state.theme]
    direction = "rtl" if st.session_state.language == "ar" else "ltr"
    align = "right" if direction == "rtl" else "left"
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
            border: none; padding: 10px 20px; font-weight: bold; transition: all 0.2s;
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
        .main-header p {{ margin: 8px 0 0 0; opacity: 0.95; }}
        .streamlit-expanderHeader {{
            background-color: {theme['card']} !important; color: {theme['text']} !important; border-radius: 8px;
        }}
        details {{ background-color: {theme['card']}; border-radius: 10px; border: 1px solid {theme['border']}; }}
        .role-badge {{
            display: inline-block; padding: 3px 12px; border-radius: 12px;
            font-size: 0.85em; font-weight: bold;
        }}
        .footer {{
            text-align: center; padding: 20px; margin-top: 40px;
            border-top: 2px solid {theme['accent']};
            color: {theme['text']}; opacity: 0.85; font-size: 0.9em;
        }}
        .footer b {{ color: {theme['accent']}; font-size: 1.05em; }}
    </style>
    """, unsafe_allow_html=True)

# ============================================================================
# 🔐 صفحات المصادقة
# ============================================================================
def render_auth_home():
    apply_theme()

    col1, col2, col3 = st.columns([1, 2, 1])
    with col1:
        selected_lang = st.selectbox(
            "🌐", list(LANGUAGES.keys()),
            format_func=lambda k: LANGUAGES[k],
            index=list(LANGUAGES.keys()).index(st.session_state.language),
            label_visibility="collapsed", key="auth_lang"
        )
        if selected_lang != st.session_state.language:
            st.session_state.language = selected_lang
            st.rerun()
    with col3:
        selected_theme = st.selectbox(
            "🎨", list(THEMES.keys()),
            index=list(THEMES.keys()).index(st.session_state.theme),
            label_visibility="collapsed", key="auth_theme"
        )
        if selected_theme != st.session_state.theme:
            st.session_state.theme = selected_theme
            st.rerun()

    st.markdown(f"""
    <div class="main-header">
        <h1>🎓 3AC RevisioMaroc</h1>
        <p>{T('auth_subtitle')}</p>
    </div>
    """, unsafe_allow_html=True)

    col1, col2, col3 = st.columns(3)

    with col1:
        st.markdown(f"""
        <div class="custom-card" style="text-align:center; min-height: 200px; border-top: 5px solid #3498DB;">
            <div style="font-size: 4em;">🎓</div>
            <h2 style="margin: 15px 0;">{T('student_login')}</h2>
            <p style="opacity: 0.8;">للتلاميذ للوصول إلى الدروس والاختبارات</p>
        </div>
        """, unsafe_allow_html=True)
        if st.button(f"🎓 {T('student_login')}", use_container_width=True, key="go_student"):
            st.session_state.auth_page = "student_login"
            st.rerun()

    with col2:
        st.markdown(f"""
        <div class="custom-card" style="text-align:center; min-height: 200px; border-top: 5px solid #E74C3C;">
            <div style="font-size: 4em;">⚙️</div>
            <h2 style="margin: 15px 0;">{T('developer_login')}</h2>
            <p style="opacity: 0.8;">للمطور Soufiane Ouhazza فقط</p>
        </div>
        """, unsafe_allow_html=True)
        if st.button(f"⚙️ {T('developer_login')}", use_container_width=True, key="go_dev"):
            st.session_state.auth_page = "developer_login"
            st.rerun()

    with col3:
        st.markdown(f"""
        <div class="custom-card" style="text-align:center; min-height: 200px; border-top: 5px solid #27AE60;">
            <div style="font-size: 4em;">📝</div>
            <h2 style="margin: 15px 0;">{T('register')}</h2>
            <p style="opacity: 0.8;">أنشئ حسابك الجديد</p>
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
        © 2026 <b>Soufiane Ouhazza</b> — 3AC RevisioMaroc<br>
        All Rights Reserved
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

            submitted = st.form_submit_button(f"🎓 {T('login_btn')}", use_container_width=True)
            if submitted:
                if not username or not password:
                    st.error(T('name_required'))
                else:
                    ok, user = authenticate(username, password)
                    if ok and user["role"] == "student":
                        st.session_state.authenticated = True
                        st.session_state.username = username
                        st.session_state.user_role = "student"
                        st.session_state.full_name = user.get("full_name", username)
                        st.session_state.student_name = user.get("full_name", username)
                        st.session_state.auth_page = "home"
                        st.rerun()
                    elif ok and user["role"] == "developer":
                        st.error("❌ هذا حساب مطور — استخدم صفحة دخول المطور")
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

    st.markdown(f"""
    <div class="footer">
        © 2026 <b>Soufiane Ouhazza</b> — All Rights Reserved
    </div>
    """, unsafe_allow_html=True)


def render_developer_login():
    apply_theme()

    st.markdown(f"""
    <div class="main-header" style="background: linear-gradient(135deg, #A50044, #004D98);">
        <h1>{T('developer_login_title')}</h1>
        <p>{T('developer_login_subtitle')}</p>
    </div>
    """, unsafe_allow_html=True)

    st.markdown(f"""
    <div class="custom-card" style="text-align:center; border-left: 5px solid #00D26A;">
        <p style="margin:0;">🔒 {T('dev_only_note')}</p>
        <p style="margin:5px 0; opacity: 0.7; font-size: 0.85em;">المطور: Soufiane Ouhazza</p>
    </div>
    """, unsafe_allow_html=True)

    col1, col2, col3 = st.columns([1, 2, 1])
    with col2:
        with st.form("dev_login_form"):
            username = st.text_input(f"👤 {T('username')}", key="dl_user")
            password = st.text_input(f"🔒 {T('password')}", type="password", key="dl_pass")

            submitted = st.form_submit_button(f"⚙️ {T('login_btn')}", use_container_width=True)
            if submitted:
                if not username or not password:
                    st.error(T('name_required'))
                else:
                    ok, user = authenticate(username, password)
                    if ok and user["role"] == "developer":
                        st.session_state.authenticated = True
                        st.session_state.username = username
                        st.session_state.user_role = "developer"
                        st.session_state.full_name = user.get("full_name", username)
                        st.session_state.student_name = user.get("full_name", username)
                        st.session_state.auth_page = "home"
                        st.rerun()
                    else:
                        st.error(T('wrong_creds'))

        st.markdown("---")
        if st.button(T('back_to_login'), use_container_width=True, key="dl_back"):
            st.session_state.auth_page = "home"
            st.rerun()

    st.markdown(f"""
    <div class="footer">
        © 2026 <b>Soufiane Ouhazza</b> — All Rights Reserved
    </div>
    """, unsafe_allow_html=True)


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

            submitted = st.form_submit_button(f"📝 {T('register_btn')}", use_container_width=True)
            if submitted:
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

    st.markdown(f"""
    <div class="footer">
        © 2026 <b>Soufiane Ouhazza</b> — All Rights Reserved
    </div>
    """, unsafe_allow_html=True)


def render_auth_page():
    auth_page = st.session_state.auth_page
    if auth_page == "home":
        render_auth_home()
    elif auth_page == "student_login":
        render_student_login()
    elif auth_page == "developer_login":
        render_developer_login()
    elif auth_page == "register":
        render_register()
    else:
        render_auth_home()

# ============================================================================
# 🏠 الرئيسية
# ============================================================================
def render_dashboard():
    name = st.session_state.student_name or T('welcome')
    st.markdown(f"""
    <div class="main-header">
        <h1>🎓 {T('welcome')} {name}!</h1>
        <p>{T('subtitle')}</p>
    </div>
    """, unsafe_allow_html=True)

    st.markdown(f"### {T('stats')}")
    c1, c2, c3, c4 = st.columns(4)
    with c1: st.metric(f"🏆 {T('points')}", st.session_state.points)
    with c2: st.metric(f"⭐ {T('level')}", st.session_state.level)
    with c3: st.metric(f"📚 {T('subjects_count')}", len(SUBJECTS))
    with c4: st.metric(f"✅ {T('progress')}", f"{get_progress_percent()}%")

    st.markdown("---")
    st.markdown(f"### 📖 {T('choose_subject')}")

    cols = st.columns(4)
    for idx, (key, info) in enumerate(SUBJECTS.items()):
        with cols[idx % 4]:
            st.markdown(f"""
            <div class="custom-card" style="text-align:center; border-top: 4px solid {info['color']};">
                <div style="font-size: 3em;">{info['icon']}</div>
                <h3 style="margin: 10px 0;">{get_subject_name(key)}</h3>
            </div>
            """, unsafe_allow_html=True)
            if st.button(T('start_review'), key=f"subj_{key}", use_container_width=True):
                st.session_state.selected_subject = key
                st.session_state.page = "lessons"
                st.rerun()

    st.markdown("---")
    st.info(T('tips'))

# ============================================================================
# 📚 الدروس
# ============================================================================
def render_lessons():
    st.markdown(f"## 📚 {T('lessons_bank')}")

    subject_keys = list(SUBJECTS.keys())
    default_idx = subject_keys.index(st.session_state.selected_subject) if st.session_state.selected_subject else 0
    selected = st.selectbox(
        T('choose_lesson_subject'), subject_keys,
        format_func=lambda k: f"{SUBJECTS[k]['icon']} {get_subject_name(k)}",
        index=default_idx
    )
    st.session_state.selected_subject = selected

    st.markdown("---")

    lessons = load_lessons(selected, st.session_state.language, owner="public")

    if not lessons:
        st.warning(T('no_lessons'))
        return

    st.markdown(f"### {T('owner_public')}")
    for lesson in lessons:
        _render_lesson_card(lesson)


def _render_lesson_card(lesson, is_personal=False):
    with st.expander(f"📖 {lesson['title']}", expanded=False):
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
            st.rerun()

# ============================================================================
# 📝 الاختبارات
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
            st.rerun()
        return

    lesson_id = st.session_state.selected_lesson
    questions = load_questions(lesson_id)

    if not questions:
        st.warning(T('no_questions'))
        if st.button(T('back')):
            st.session_state.selected_lesson = None
            st.rerun()
        return

    st.markdown(f"""
    <div class="custom-card">
        <h3>📝 {T('quiz_of')} {st.session_state.get('current_lesson_title', '')}</h3>
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
                st.session_state.quiz_state = {}
                st.session_state.quiz_finished = False
                st.rerun()
        with c2:
            if st.button(T('choose_another'), use_container_width=True):
                st.session_state.selected_lesson = None
                st.session_state.quiz_finished = False
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
            add_points(score * 10)
            st.rerun()

# ============================================================================
# ⚙️ لوحة المطور
# ============================================================================
def render_developer_panel():
    if st.session_state.user_role != "developer":
        st.error("🔒 هذه اللوحة محمية — للمطور فقط")
        st.stop()

    st.markdown(f"## ⚙️ {T('developer_panel')}")
    st.caption(f"👨‍💻 {T('dev_only_note')}")

    tab1, tab2 = st.tabs([T('manage_lessons'), T('manage_questions')])

    with tab1:
        st.markdown(f"### {T('add_lesson')}")

        with st.form("add_lesson_form", clear_on_submit=True):
            c1, c2 = st.columns(2)
            with c1:
                subject = st.selectbox(T('lesson_subject'), list(SUBJECTS.keys()),
                                       format_func=lambda k: f"{SUBJECTS[k]['icon']} {get_subject_name(k)}")
            with c2:
                language = st.selectbox(T('lesson_language'), list(LANGUAGES.keys()),
                                        format_func=lambda k: LANGUAGES[k])

            title = st.text_input(T('lesson_title'))
            content = st.text_area(f"{T('lesson_content_label')} {T('lesson_content_optional')}", height=150)

            c1, c2 = st.columns(2)
            with c1:
                image_file = st.file_uploader(T('lesson_image'), type=["png", "jpg", "jpeg", "webp"])
            with c2:
                pdf_file = st.file_uploader(T('lesson_pdf'), type=["pdf"])

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

        found_any = False
        for subj_key in SUBJECTS.keys():
            for lang_key in LANGUAGES.keys():
                lessons = load_lessons(subj_key, lang_key, owner="public")
                if lessons:
                    found_any = True
                    st.markdown(f"**{get_subject_name(subj_key)} / {LANGUAGES[lang_key]}**")
                    for lesson in lessons:
                        c1, c2 = st.columns([5, 1])
                        with c1:
                            icons = ""
                            if lesson.get('content'): icons += "📝"
                            if lesson.get('image_url'): icons += "📷"
                            if lesson.get('pdf_url'): icons += "📄"
                            st.markdown(f"{icons} **{lesson['title']}**")
                        with c2:
                            if st.button("🗑️", key=f"del_lesson_{lesson['id']}"):
                                if delete_lesson(lesson['id'], owner_filter="public"):
                                    st.success(T('deleted'))
                                    st.rerun()
                    st.markdown("---")

        if not found_any:
            st.info(T('no_custom_lessons'))

    with tab2:
        st.markdown(f"### {T('add_question')}")

        all_lessons = load_lessons(owner="public")
        lesson_options = {str(l['id']): f"[{get_subject_name(l['subject'])} / {LANGUAGES[l['language']]}] {l['title']}" for l in all_lessons}

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
                        st.error("⚠️ املأ جميع الحقول")

        st.markdown("---")
        st.markdown(f"### {T('manage_questions')}")

        found_any_q = False
        for l in all_lessons:
            qs = load_questions(l['id'])
            if qs:
                found_any_q = True
                st.markdown(f"**📖 {lesson_options.get(str(l['id']), l['title'])}**")
                for q in qs:
                    c1, c2 = st.columns([5, 1])
                    with c1:
                        st.markdown(f"❓ {q['question']} — ✅ **{chr(65+q['correct'])}**")
                    with c2:
                        if st.button("🗑️", key=f"del_q_{q['id']}"):
                            if delete_question(q['id']):
                                st.success(T('deleted'))
                                st.rerun()
                st.markdown("---")

        if not found_any_q:
            st.info(T('no_custom_questions'))

# ============================================================================
# 🚀 التوجيه الرئيسي
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
        <p style="opacity:0.7;">{T('app_name')}</p>
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

    st.markdown("---")

    st.markdown(f"### {T('language')}")
    lang_keys = list(LANGUAGES.keys())
    selected_lang = st.selectbox(T('choose_language'), lang_keys,
                                  format_func=lambda k: LANGUAGES[k],
                                  index=lang_keys.index(st.session_state.language),
                                  label_visibility="collapsed")
    if selected_lang != st.session_state.language:
        st.session_state.language = selected_lang
        st.rerun()

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
        st.rerun()
    if st.button(T('lessons'), use_container_width=True):
        st.session_state.page = "lessons"
        st.rerun()
    if st.button(T('quizzes'), use_container_width=True):
        st.session_state.page = "quiz"
        st.session_state.selected_lesson = None
        st.rerun()

    if st.session_state.user_role == "developer":
        if st.button(T('developer'), use_container_width=True):
            st.session_state.page = "developer"
            st.rerun()

    st.markdown("---")

    if st.session_state.user_role in ["student", "guest"]:
        st.markdown(f"### {T('your_progress')}")
        c1, c2 = st.columns(2)
        with c1: st.metric(T('points'), st.session_state.points)
        with c2: st.metric(T('level'), st.session_state.level)
        st.progress(get_progress_percent() / 100)
        st.caption(f"{T('level_progress')}: {get_progress_percent()}%")
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
    st.error("🔒 هذه الصفحة محمية — للمطور فقط")
    st.session_state.page = "dashboard"
    st.rerun()

if page == "dashboard":
    render_dashboard()
elif page == "lessons":
    render_lessons()
elif page == "quiz":
    render_quiz()
elif page == "developer" and st.session_state.user_role == "developer":
    render_developer_panel()
else:
    render_dashboard()

st.markdown(f"""
<div class="footer">
    © 2026 <b>Soufiane Ouhazza</b> — 3AC RevisioMaroc<br>
    All Rights Reserved
</div>
""", unsafe_allow_html=True)
