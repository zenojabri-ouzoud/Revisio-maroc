# ============================================================================
# 3AC RevisioMaroc - النسخة الاحترافية الكاملة
# ============================================================================
# التثبيت:
#   pip install streamlit supabase pandas
#
# التشغيل:
#   streamlit run app.py
# ============================================================================

import streamlit as st
import hashlib
import json
import os
from datetime import datetime

# ----------------------------------------------------------------------------
# محاولة الاتصال بـ Supabase (اختياري)
# ----------------------------------------------------------------------------
try:
    from supabase import create_client, Client
    SUPABASE_AVAILABLE = True
except ImportError:
    SUPABASE_AVAILABLE = False

# ============================================================================
# 📊 هيكل جداول Supabase المقترح (مع نظام المستخدمين)
# ============================================================================
"""
-- جدول المستخدمين
CREATE TABLE users (
    id SERIAL PRIMARY KEY,
    username TEXT UNIQUE NOT NULL,
    password_hash TEXT NOT NULL,
    role TEXT NOT NULL DEFAULT 'student',   -- student, developer
    full_name TEXT,
    created_at TIMESTAMP DEFAULT NOW()
);

-- جدول الدروس
CREATE TABLE lessons (
    id SERIAL PRIMARY KEY,
    subject TEXT NOT NULL,
    language TEXT NOT NULL,
    title TEXT NOT NULL,
    content TEXT NOT NULL,
    created_at TIMESTAMP DEFAULT NOW()
);

-- جدول الأسئلة
CREATE TABLE questions (
    id SERIAL PRIMARY KEY,
    lesson_id TEXT NOT NULL,
    question TEXT NOT NULL,
    option_a TEXT NOT NULL,
    option_b TEXT NOT NULL,
    option_c TEXT NOT NULL,
    option_d TEXT NOT NULL,
    correct_answer TEXT NOT NULL,
    explanation TEXT,
    created_at TIMESTAMP DEFAULT NOW()
);

-- إنشاء حساب المطور الافتراضي
-- (كلمة المرور: admin123 - سيتم تشفيرها بـ SHA256)
"""
# ============================================================================

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
# مسار ملفات التخزين المحلي
# ----------------------------------------------------------------------------
DATA_DIR = "data"
USERS_FILE = os.path.join(DATA_DIR, "users.json")
CUSTOM_LESSONS_FILE = os.path.join(DATA_DIR, "custom_lessons.json")
CUSTOM_QUESTIONS_FILE = os.path.join(DATA_DIR, "custom_questions.json")

os.makedirs(DATA_DIR, exist_ok=True)

# ----------------------------------------------------------------------------
# دوال تشفير كلمة المرور
# ----------------------------------------------------------------------------
def hash_password(password):
    return hashlib.sha256(password.encode()).hexdigest()

# ----------------------------------------------------------------------------
# إدارة المستخدمين
# ----------------------------------------------------------------------------
def load_users():
    if os.path.exists(USERS_FILE):
        with open(USERS_FILE, "r", encoding="utf-8") as f:
            return json.load(f)
    # إنشاء حساب مطور افتراضي
    default_users = {
        "admin": {
            "password": hash_password("admin123"),
            "role": "developer",
            "full_name": "المطور الرئيسي"
        }
    }
    save_users(default_users)
    return default_users

def save_users(users):
    with open(USERS_FILE, "w", encoding="utf-8") as f:
        json.dump(users, f, ensure_ascii=False, indent=2)

def register_user(username, password, full_name=""):
    users = load_users()
    if username in users:
        return False, "❌ اسم المستخدم موجود مسبقاً"
    if len(password) < 4:
        return False, "❌ كلمة المرور قصيرة جداً (4 أحرف على الأقل)"
    users[username] = {
        "password": hash_password(password),
        "role": "student",
        "full_name": full_name or username
    }
    save_users(users)
    return True, "✅ تم إنشاء الحساب بنجاح"

def authenticate(username, password):
    users = load_users()
    if username in users and users[username]["password"] == hash_password(password):
        return True, users[username]
    return False, None

# ----------------------------------------------------------------------------
# إدارة الدروس والأسئلة المخصصة (يضيفها المطور)
# ----------------------------------------------------------------------------
def load_custom_lessons():
    if os.path.exists(CUSTOM_LESSONS_FILE):
        with open(CUSTOM_LESSONS_FILE, "r", encoding="utf-8") as f:
            return json.load(f)
    return {}

def save_custom_lessons(data):
    with open(CUSTOM_LESSONS_FILE, "w", encoding="utf-8") as f:
        json.dump(data, f, ensure_ascii=False, indent=2)

def load_custom_questions():
    if os.path.exists(CUSTOM_QUESTIONS_FILE):
        with open(CUSTOM_QUESTIONS_FILE, "r", encoding="utf-8") as f:
            return json.load(f)
    return {}

def save_custom_questions(data):
    with open(CUSTOM_QUESTIONS_FILE, "w", encoding="utf-8") as f:
        json.dump(data, f, ensure_ascii=False, indent=2)

# ----------------------------------------------------------------------------
# 🌐 الترجمات
# ----------------------------------------------------------------------------
TRANSLATIONS = {
    "ar": {
        "app_name": "منصة المراجعة الشاملة",
        "dir": "rtl",
        "dashboard": "🏠 الرئيسية",
        "lessons": "📚 الدروس",
        "quizzes": "📝 الاختبارات",
        "developer": "⚙️ لوحة المطور",
        "welcome": "مرحباً",
        "subtitle": "منصة 3AC RevisioMaroc لمراجعة شاملة لجميع المواد الدراسية",
        "stats": "📊 إحصائياتك",
        "points": "النقاط",
        "level": "المستوى",
        "subjects_count": "المواد",
        "progress": "التقدم",
        "choose_subject": "اختر مادة للمراجعة",
        "start_review": "ابدأ المراجعة",
        "tips": "💡 نصيحة: راجع الدروس أولاً، ثم اختبر نفسك!",
        "lessons_bank": "بنك الملخصات والدروس",
        "choose_lesson_subject": "اختر المادة",
        "quiz_lesson": "📝 اختبار هذا الدرس",
        "no_lessons": "⚠️ لا توجد دروس متاحة لهذه المادة حالياً",
        "smart_quizzes": "الاختبارات الذكية",
        "choose_lesson": "اختر الدرس",
        "start_quiz": "🚀 بدء الاختبار",
        "questions_count": "عدد الأسئلة",
        "each_correct": "كل إجابة صحيحة = 10 نقاط",
        "final_score": "🎯 نتيجتك النهائية",
        "excellent": "🏆 ممتاز! أداء رائع",
        "good": "👍 جيد! واصل المجهود",
        "needs_review": "📚 يحتاج إلى مراجعة",
        "correction": "✅ التصحيح",
        "question": "السؤال",
        "explanation": "التفسير",
        "retry": "🔄 إعادة الاختبار",
        "choose_another": "🔙 اختيار درس آخر",
        "submit": "✅ تسليم الإجابات",
        "select_answer": "اختر الإجابة",
        "student_name": "الاسم",
        "student_info": "👤 معلومات التلميذ",
        "menu": "📌 القائمة",
        "your_progress": "🏆 تقدمك",
        "level_progress": "التقدم في المستوى",
        "theme": "🎨 اختر الثيم",
        "appearance": "المظهر",
        "language": "🌐 اللغة",
        "choose_language": "اختر لغة الواجهة",
        "congrats": "🎉 مبروك! ارتقيت إلى المستوى",
        "no_questions": "⚠️ لا توجد أسئلة متاحة",
        "back": "🔙 رجوع",
        "quiz_of": "اختبار:",
        "no_lessons_quiz": "⚠️ لا توجد دروس متاحة",
        # Auth
        "login": "🔐 تسجيل الدخول",
        "register": "📝 إنشاء حساب",
        "guest": "👤 الدخول كزائر",
        "username": "اسم المستخدم",
        "password": "كلمة المرور",
        "full_name": "الاسم الكامل",
        "login_btn": "دخول",
        "register_btn": "تسجيل",
        "logout": "🚪 تسجيل الخروج",
        "auth_title": "مرحباً بك في 3AC RevisioMaroc",
        "auth_subtitle": "سجّل دخولك أو ادخل كزائر للبدء",
        "wrong_creds": "❌ اسم المستخدم أو كلمة المرور خاطئة",
        "login_success": "✅ تم تسجيل الدخول بنجاح",
        "guest_note": "💡 كزائر: يمكنك تصفح الدروس والاختبارات، لكن لن تُحفظ نتائجك.",
        "logged_as": "مسجل الدخول كـ",
        "role_student": "تلميذ",
        "role_developer": "مطور",
        "role_guest": "زائر",
        "developer_panel": "لوحة تحكم المطور",
        "add_lesson": "➕ إضافة درس جديد",
        "add_question": "➕ إضافة سؤال جديد",
        "manage_lessons": "📋 إدارة الدروس",
        "manage_questions": "❓ إدارة الأسئلة",
        "lesson_title": "عنوان الدرس",
        "lesson_content": "محتوى الدرس",
        "lesson_subject": "المادة",
        "lesson_language": "اللغة",
        "lesson_id": "معرّف الدرس",
        "save_lesson": "💾 حفظ الدرس",
        "lesson_saved": "✅ تم حفظ الدرس بنجاح",
        "question_text": "نص السؤال",
        "option_a": "الخيار A",
        "option_b": "الخيار B",
        "option_c": "الخيار C",
        "option_d": "الخيار D",
        "correct_answer": "الإجابة الصحيحة",
        "explanation_text": "التفسير (اختياري)",
        "save_question": "💾 حفظ السؤال",
        "question_saved": "✅ تم حفظ السؤال بنجاح",
        "select_lesson_for_question": "اختر الدرس المرتبط بالسؤال",
        "delete_lesson": "🗑️ حذف",
        "delete_question": "🗑️ حذف",
        "confirm_delete": "هل أنت متأكد من الحذف؟",
        "deleted": "✅ تم الحذف",
        "no_custom_lessons": "لا توجد دروس مخصصة بعد",
        "no_custom_questions": "لا توجد أسئلة مخصصة بعد",
    },
    "fr": {
        "app_name": "Plateforme de révision complète",
        "dir": "ltr",
        "dashboard": "🏠 Accueil",
        "lessons": "📚 Leçons",
        "quizzes": "📝 Quiz",
        "developer": "⚙️ Panneau Dev",
        "welcome": "Bienvenue",
        "subtitle": "3AC RevisioMaroc - Révisez toutes les matières",
        "stats": "📊 Statistiques",
        "points": "Points",
        "level": "Niveau",
        "subjects_count": "Matières",
        "progress": "Progrès",
        "choose_subject": "Choisissez une matière",
        "start_review": "Commencer",
        "tips": "💡 Révisez puis testez-vous !",
        "lessons_bank": "Banque de leçons",
        "choose_lesson_subject": "Choisir la matière",
        "quiz_lesson": "📝 Quiz",
        "no_lessons": "⚠️ Aucune leçon disponible",
        "smart_quizzes": "Quiz intelligents",
        "choose_lesson": "Choisir la leçon",
        "start_quiz": "🚀 Démarrer",
        "questions_count": "Nombre de questions",
        "each_correct": "Bonne réponse = 10 points",
        "final_score": "🎯 Score final",
        "excellent": "🏆 Excellent !",
        "good": "👍 Bien !",
        "needs_review": "📚 À revoir",
        "correction": "✅ Correction",
        "question": "Question",
        "explanation": "Explication",
        "retry": "🔄 Refaire",
        "choose_another": "🔙 Autre leçon",
        "submit": "✅ Soumettre",
        "select_answer": "Choisir",
        "student_name": "Nom",
        "student_info": "👤 Élève",
        "menu": "📌 Menu",
        "your_progress": "🏆 Progrès",
        "level_progress": "Progrès du niveau",
        "theme": "🎨 Thème",
        "appearance": "Apparence",
        "language": "🌐 Langue",
        "choose_language": "Choisir la langue",
        "congrats": "🎉 Bravo ! Niveau",
        "no_questions": "⚠️ Aucune question",
        "back": "🔙 Retour",
        "quiz_of": "Quiz :",
        "no_lessons_quiz": "⚠️ Aucune leçon",
        "login": "🔐 Connexion",
        "register": "📝 Inscription",
        "guest": "👤 Invité",
        "username": "Nom d'utilisateur",
        "password": "Mot de passe",
        "full_name": "Nom complet",
        "login_btn": "Connexion",
        "register_btn": "S'inscrire",
        "logout": "🚪 Déconnexion",
        "auth_title": "Bienvenue sur 3AC RevisioMaroc",
        "auth_subtitle": "Connectez-vous ou entrez comme invité",
        "wrong_creds": "❌ Identifiants incorrects",
        "login_success": "✅ Connexion réussie",
        "guest_note": "💡 Invité : naviguez librement, résultats non sauvegardés.",
        "logged_as": "Connecté en tant que",
        "role_student": "Élève",
        "role_developer": "Développeur",
        "role_guest": "Invité",
        "developer_panel": "Panneau développeur",
        "add_lesson": "➕ Ajouter leçon",
        "add_question": "➕ Ajouter question",
        "manage_lessons": "📋 Gérer leçons",
        "manage_questions": "❓ Gérer questions",
        "lesson_title": "Titre",
        "lesson_content": "Contenu",
        "lesson_subject": "Matière",
        "lesson_language": "Langue",
        "lesson_id": "ID Leçon",
        "save_lesson": "💾 Sauvegarder",
        "lesson_saved": "✅ Leçon sauvegardée",
        "question_text": "Question",
        "option_a": "Option A",
        "option_b": "Option B",
        "option_c": "Option C",
        "option_d": "Option D",
        "correct_answer": "Réponse correcte",
        "explanation_text": "Explication (optionnel)",
        "save_question": "💾 Sauvegarder",
        "question_saved": "✅ Question sauvegardée",
        "select_lesson_for_question": "Choisir la leçon",
        "delete_lesson": "🗑️ Supprimer",
        "delete_question": "🗑️ Supprimer",
        "confirm_delete": "Confirmer la suppression ?",
        "deleted": "✅ Supprimé",
        "no_custom_lessons": "Aucune leçon personnalisée",
        "no_custom_questions": "Aucune question personnalisée",
    },
    "en": {
        "app_name": "Complete Revision Platform",
        "dir": "ltr",
        "dashboard": "🏠 Home",
        "lessons": "📚 Lessons",
        "quizzes": "📝 Quizzes",
        "developer": "⚙️ Dev Panel",
        "welcome": "Welcome",
        "subtitle": "3AC RevisioMaroc - Revise all subjects",
        "stats": "📊 Your Stats",
        "points": "Points",
        "level": "Level",
        "subjects_count": "Subjects",
        "progress": "Progress",
        "choose_subject": "Choose a subject",
        "start_review": "Start",
        "tips": "💡 Review then test yourself!",
        "lessons_bank": "Lessons Bank",
        "choose_lesson_subject": "Choose subject",
        "quiz_lesson": "📝 Quiz",
        "no_lessons": "⚠️ No lessons available",
        "smart_quizzes": "Smart Quizzes",
        "choose_lesson": "Choose lesson",
        "start_quiz": "🚀 Start",
        "questions_count": "Questions",
        "each_correct": "Correct = 10 points",
        "final_score": "🎯 Final Score",
        "excellent": "🏆 Excellent!",
        "good": "👍 Good!",
        "needs_review": "📚 Needs review",
        "correction": "✅ Correction",
        "question": "Question",
        "explanation": "Explanation",
        "retry": "🔄 Retry",
        "choose_another": "🔙 Another lesson",
        "submit": "✅ Submit",
        "select_answer": "Select",
        "student_name": "Name",
        "student_info": "👤 Student",
        "menu": "📌 Menu",
        "your_progress": "🏆 Progress",
        "level_progress": "Level progress",
        "theme": "🎨 Theme",
        "appearance": "Appearance",
        "language": "🌐 Language",
        "choose_language": "Choose language",
        "congrats": "🎉 Congrats! Level",
        "no_questions": "⚠️ No questions",
        "back": "🔙 Back",
        "quiz_of": "Quiz:",
        "no_lessons_quiz": "⚠️ No lessons",
        "login": "🔐 Login",
        "register": "📝 Register",
        "guest": "👤 Guest",
        "username": "Username",
        "password": "Password",
        "full_name": "Full name",
        "login_btn": "Login",
        "register_btn": "Register",
        "logout": "🚪 Logout",
        "auth_title": "Welcome to 3AC RevisioMaroc",
        "auth_subtitle": "Login or continue as guest",
        "wrong_creds": "❌ Wrong credentials",
        "login_success": "✅ Login successful",
        "guest_note": "💡 Guest: browse freely, results not saved.",
        "logged_as": "Logged in as",
        "role_student": "Student",
        "role_developer": "Developer",
        "role_guest": "Guest",
        "developer_panel": "Developer Panel",
        "add_lesson": "➕ Add Lesson",
        "add_question": "➕ Add Question",
        "manage_lessons": "📋 Manage Lessons",
        "manage_questions": "❓ Manage Questions",
        "lesson_title": "Title",
        "lesson_content": "Content",
        "lesson_subject": "Subject",
        "lesson_language": "Language",
        "lesson_id": "Lesson ID",
        "save_lesson": "💾 Save Lesson",
        "lesson_saved": "✅ Lesson saved",
        "question_text": "Question",
        "option_a": "Option A",
        "option_b": "Option B",
        "option_c": "Option C",
        "option_d": "Option D",
        "correct_answer": "Correct Answer",
        "explanation_text": "Explanation (optional)",
        "save_question": "💾 Save Question",
        "question_saved": "✅ Question saved",
        "select_lesson_for_question": "Select lesson",
        "delete_lesson": "🗑️ Delete",
        "delete_question": "🗑️ Delete",
        "confirm_delete": "Confirm delete?",
        "deleted": "✅ Deleted",
        "no_custom_lessons": "No custom lessons yet",
        "no_custom_questions": "No custom questions yet",
    },
    "es": {
        "app_name": "Plataforma de revisión",
        "dir": "ltr",
        "dashboard": "🏠 Inicio",
        "lessons": "📚 Lecciones",
        "quizzes": "📝 Cuestionarios",
        "developer": "⚙️ Panel Dev",
        "welcome": "Bienvenido",
        "subtitle": "3AC RevisioMaroc - Revisa todas las materias",
        "stats": "📊 Estadísticas",
        "points": "Puntos",
        "level": "Nivel",
        "subjects_count": "Materias",
        "progress": "Progreso",
        "choose_subject": "Elige materia",
        "start_review": "Comenzar",
        "tips": "💡 ¡Revisa y pruébate!",
        "lessons_bank": "Banco de lecciones",
        "choose_lesson_subject": "Elegir materia",
        "quiz_lesson": "📝 Cuestionario",
        "no_lessons": "⚠️ No hay lecciones",
        "smart_quizzes": "Cuestionarios",
        "choose_lesson": "Elegir lección",
        "start_quiz": "🚀 Iniciar",
        "questions_count": "Preguntas",
        "each_correct": "Correcta = 10 puntos",
        "final_score": "🎯 Puntuación",
        "excellent": "🏆 ¡Excelente!",
        "good": "👍 ¡Bien!",
        "needs_review": "📚 Necesita repaso",
        "correction": "✅ Corrección",
        "question": "Pregunta",
        "explanation": "Explicación",
        "retry": "🔄 Reintentar",
        "choose_another": "🔙 Otra lección",
        "submit": "✅ Enviar",
        "select_answer": "Elegir",
        "student_name": "Nombre",
        "student_info": "👤 Estudiante",
        "menu": "📌 Menú",
        "your_progress": "🏆 Progreso",
        "level_progress": "Progreso del nivel",
        "theme": "🎨 Tema",
        "appearance": "Apariencia",
        "language": "🌐 Idioma",
        "choose_language": "Elegir idioma",
        "congrats": "🎉 ¡Felicidades! Nivel",
        "no_questions": "⚠️ No hay preguntas",
        "back": "🔙 Volver",
        "quiz_of": "Cuestionario:",
        "no_lessons_quiz": "⚠️ No hay lecciones",
        "login": "🔐 Iniciar sesión",
        "register": "📝 Registrarse",
        "guest": "👤 Invitado",
        "username": "Usuario",
        "password": "Contraseña",
        "full_name": "Nombre completo",
        "login_btn": "Entrar",
        "register_btn": "Registrar",
        "logout": "🚪 Salir",
        "auth_title": "Bienvenido a 3AC RevisioMaroc",
        "auth_subtitle": "Inicia sesión o entra como invitado",
        "wrong_creds": "❌ Credenciales incorrectas",
        "login_success": "✅ Sesión iniciada",
        "guest_note": "💡 Invitado: navega libremente, resultados no guardados.",
        "logged_as": "Sesión de",
        "role_student": "Estudiante",
        "role_developer": "Desarrollador",
        "role_guest": "Invitado",
        "developer_panel": "Panel del desarrollador",
        "add_lesson": "➕ Añadir lección",
        "add_question": "➕ Añadir pregunta",
        "manage_lessons": "📋 Gestionar lecciones",
        "manage_questions": "❓ Gestionar preguntas",
        "lesson_title": "Título",
        "lesson_content": "Contenido",
        "lesson_subject": "Materia",
        "lesson_language": "Idioma",
        "lesson_id": "ID Lección",
        "save_lesson": "💾 Guardar",
        "lesson_saved": "✅ Lección guardada",
        "question_text": "Pregunta",
        "option_a": "Opción A",
        "option_b": "Opción B",
        "option_c": "Opción C",
        "option_d": "Opción D",
        "correct_answer": "Respuesta correcta",
        "explanation_text": "Explicación (opcional)",
        "save_question": "💾 Guardar",
        "question_saved": "✅ Pregunta guardada",
        "select_lesson_for_question": "Elegir lección",
        "delete_lesson": "🗑️ Eliminar",
        "delete_question": "🗑️ Eliminar",
        "confirm_delete": "¿Confirmar eliminación?",
        "deleted": "✅ Eliminado",
        "no_custom_lessons": "Sin lecciones personalizadas",
        "no_custom_questions": "Sin preguntas personalizadas",
    },
}

LANGUAGES = {
    "ar": "🇲🇦 العربية",
    "fr": "🇫🇷 Français",
    "en": "🇬🇧 English",
    "es": "🇪🇸 Español",
}

# ----------------------------------------------------------------------------
# الثيمات
# ----------------------------------------------------------------------------
THEMES = {
    "🌙 Dark": {"bg": "#0E1117", "card": "#1E2530", "text": "#FAFAFA", "accent": "#4A90E2", "secondary": "#262730", "border": "#3A4050"},
    "☀️ Light": {"bg": "#F5F7FA", "card": "#FFFFFF", "text": "#1A1A1A", "accent": "#2563EB", "secondary": "#E8EBF0", "border": "#D1D5DB"},
    "🌊 Ocean Blue": {"bg": "#0B1E2D", "card": "#12304A", "text": "#E6F2FF", "accent": "#00B4D8", "secondary": "#1B4159", "border": "#256D85"},
    "🌅 Sunset": {"bg": "#2B1216", "card": "#3D1A21", "text": "#FFE8D6", "accent": "#FF7B54", "secondary": "#4A2028", "border": "#8B3A42"},
    "🌿 Emerald": {"bg": "#0F2027", "card": "#1B3A2F", "text": "#E8F5E9", "accent": "#26A69A", "secondary": "#234A3B", "border": "#2E7D6B"},
}

# ----------------------------------------------------------------------------
# المواد
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
# 📚 الدروس الأساسية
# ----------------------------------------------------------------------------
LESSONS_DB = {
    "maths": {
        "ar": [
            {"id": "m_ar_1", "title": "الأعداد الجذرية", "content": "**تعريف:** العدد الجذري هو كل عدد على شكل √a.\n\n**الخصائص:**\n- √(a × b) = √a × √b\n- (√a)² = a\n\n**مثال:** √8 = 2√2"},
            {"id": "m_ar_2", "title": "مبرهنة فيتاغورس", "content": "**النص:** في مثلث قائم الزاوية، مربع الوتر يساوي مجموع مربعي الضلعين الآخرين.\n\n**الصيغة:** BC² = AB² + AC²"},
        ],
        "fr": [
            {"id": "m_fr_1", "title": "Les racines carrées", "content": "**Définition :** La racine carrée d'un nombre positif a.\n\n**Propriétés :**\n- √(a × b) = √a × √b\n- (√a)² = a"},
        ],
        "en": [
            {"id": "m_en_1", "title": "Square Roots", "content": "**Definition:** The square root of a positive number a.\n\n**Properties:**\n- √(a × b) = √a × √b\n- (√a)² = a"},
        ],
        "es": [
            {"id": "m_es_1", "title": "Raíces cuadradas", "content": "**Definición:** La raíz cuadrada de un número positivo a.\n\n**Propiedades:**\n- √(a × b) = √a × √b\n- (√a)² = a"},
        ],
    },
    "french": {
        "ar": [{"id": "f_ar_1", "title": "المضارع البسيط", "content": "**النهايات:** -e, -es, -e, -ons, -ez, -ent\n\n**مثال:** Je parle, tu parles..."}],
        "fr": [{"id": "f_fr_1", "title": "Le présent de l'indicatif", "content": "**Terminaisons :** -e, -es, -e, -ons, -ez, -ent\n\n**Exemple :** Je parle, tu parles..."}],
        "en": [{"id": "f_en_1", "title": "French Present Tense", "content": "**Endings:** -e, -es, -e, -ons, -ez, -ent"}],
        "es": [{"id": "f_es_1", "title": "Presente (francés)", "content": "**Terminaciones:** -e, -es, -e, -ons, -ez, -ent"}],
    },
    "english": {
        "ar": [{"id": "e_ar_1", "title": "المضارع البسيط", "content": "**الاستخدام:** العادات والروتين\n\n**مثال:** I study every day."}],
        "fr": [{"id": "e_fr_1", "title": "Le Présent Simple", "content": "**Usage :** Habitudes et routines\n\n**Exemple :** I study every day."}],
        "en": [{"id": "e_en_1", "title": "Present Simple", "content": "**Usage:** Habits and routines\n\n**Example:** I study every day."}],
        "es": [{"id": "e_es_1", "title": "Presente Simple", "content": "**Uso:** Hábitos y rutinas\n\n**Ejemplo:** I study every day."}],
    },
    "history": {
        "ar": [{"id": "h_ar_1", "title": "الحرب العالمية الأولى", "content": "**التواريخ:**\n- 1914: البداية\n- 1918: النهاية"}],
        "fr": [{"id": "h_fr_1", "title": "La Première Guerre mondiale", "content": "**Dates :**\n- 1914 : Début\n- 1918 : Fin"}],
        "en": [{"id": "h_en_1", "title": "World War I", "content": "**Dates:**\n- 1914: Start\n- 1918: End"}],
        "es": [{"id": "h_es_1", "title": "Primera Guerra Mundial", "content": "**Fechas:**\n- 1914: Inicio\n- 1918: Fin"}],
    },
    "islamic": {
        "ar": [{"id": "i_ar_1", "title": "أحكام التجويد", "content": "**الإظهار:** إظهار النون الساكنة عند حروف الحلق."}],
        "fr": [{"id": "i_fr_1", "title": "Règles du Tajwid", "content": "**Izhar :** Prononcer clairement le Noun Sakina."}],
        "en": [{"id": "i_en_1", "title": "Tajwid Rules", "content": "**Izhar:** Clear pronunciation of Noon Sakinah."}],
        "es": [{"id": "i_es_1", "title": "Reglas del Tajwid", "content": "**Izhar:** Pronunciación clara de Nun Sakinah."}],
    },
    "pc": {
        "ar": [{"id": "p_ar_1", "title": "التيار الكهربائي", "content": "**التعريف:** حركة منظمة للإلكترونات.\n\n**الوحدة:** الأمبير (A)"}],
        "fr": [{"id": "p_fr_1", "title": "Le courant électrique", "content": "**Définition :** Déplacement ordonné d'électrons.\n\n**Unité :** Ampère (A)"}],
        "en": [{"id": "p_en_1", "title": "Electric Current", "content": "**Definition:** Ordered movement of electrons.\n\n**Unit:** Ampere (A)"}],
        "es": [{"id": "p_es_1", "title": "Corriente eléctrica", "content": "**Definición:** Movimiento ordenado de electrones.\n\n**Unidad:** Amperio (A)"}],
    },
    "svt": {
        "ar": [{"id": "s_ar_1", "title": "التنفس عند الإنسان", "content": "**المراحل:**\n1. الشهيق\n2. التبادل الغازي\n3. الزفير"}],
        "fr": [{"id": "s_fr_1", "title": "La respiration", "content": "**Étapes :**\n1. Inspiration\n2. Échange gazeux\n3. Expiration"}],
        "en": [{"id": "s_en_1", "title": "Human Respiration", "content": "**Stages:**\n1. Inhalation\n2. Gas exchange\n3. Exhalation"}],
        "es": [{"id": "s_es_1", "title": "La respiración", "content": "**Etapas:**\n1. Inspiración\n2. Intercambio\n3. Espiración"}],
    },
}

# ----------------------------------------------------------------------------
# 📝 الأسئلة الأساسية
# ----------------------------------------------------------------------------
QUESTIONS_DB = {
    "m_ar_1": [
        {"question": "ما هو تبسيط √50؟", "options": ["5√2", "2√5", "25√2", "10√5"], "correct": 0, "explanation": "√50 = √(25×2) = 5√2"},
        {"question": "ما قيمة (√7)²؟", "options": ["14", "7", "49", "√7"], "correct": 1, "explanation": "(√a)² = a"},
    ],
    "m_ar_2": [
        {"question": "في مثلث قائم، الضلعان 3 و 4. الوتر؟", "options": ["5", "6", "7", "12"], "correct": 0, "explanation": "BC² = 9+16 = 25 → BC=5"},
    ],
    "m_fr_1": [
        {"question": "Quel est √50 ?", "options": ["5√2", "2√5", "25√2", "10√5"], "correct": 0, "explanation": "√50 = 5√2"},
    ],
    "m_en_1": [
        {"question": "Simplified √50?", "options": ["5√2", "2√5", "25√2", "10√5"], "correct": 0, "explanation": "√50 = 5√2"},
    ],
    "m_es_1": [
        {"question": "¿√50 simplificado?", "options": ["5√2", "2√5", "25√2", "10√5"], "correct": 0, "explanation": "√50 = 5√2"},
    ],
    "f_ar_1": [
        {"question": "نهاية 'parler' مع 'nous'؟", "options": ["-ons", "-ez", "-ent", "-es"], "correct": 0, "explanation": "Nous parlons"},
    ],
    "f_fr_1": [
        {"question": "Terminaison de 'parler' à 'nous' ?", "options": ["-ons", "-ez", "-ent", "-es"], "correct": 0, "explanation": "Nous parlons"},
    ],
    "f_en_1": [
        {"question": "Ending of 'parler' with 'nous'?", "options": ["-ons", "-ez", "-ent", "-es"], "correct": 0, "explanation": "Nous parlons"},
    ],
    "f_es_1": [
        {"question": "¿Terminación de 'parler' con 'nous'?", "options": ["-ons", "-ez", "-ent", "-es"], "correct": 0, "explanation": "Nous parlons"},
    ],
    "e_ar_1": [
        {"question": "She ___ English every day.", "options": ["study", "studies", "studying", "studied"], "correct": 1, "explanation": "الغائب المفرد: studies"},
    ],
    "e_fr_1": [
        {"question": "She ___ English every day.", "options": ["study", "studies", "studying", "studied"], "correct": 1, "explanation": "3ème personne: studies"},
    ],
    "e_en_1": [
        {"question": "She ___ English every day.", "options": ["study", "studies", "studying", "studied"], "correct": 1, "explanation": "3rd person: studies"},
    ],
    "e_es_1": [
        {"question": "She ___ English every day.", "options": ["study", "studies", "studying", "studied"], "correct": 1, "explanation": "3ª persona: studies"},
    ],
    "h_ar_1": [
        {"question": "متى بدأت الحرب العالمية الأولى؟", "options": ["1912", "1914", "1918", "1939"], "correct": 1, "explanation": "سنة 1914"},
    ],
    "h_fr_1": [
        {"question": "Début de la 1ère Guerre mondiale ?", "options": ["1912", "1914", "1918", "1939"], "correct": 1, "explanation": "En 1914"},
    ],
    "h_en_1": [
        {"question": "When did WWI begin?", "options": ["1912", "1914", "1918", "1939"], "correct": 1, "explanation": "In 1914"},
    ],
    "h_es_1": [
        {"question": "¿Cuándo comenzó la 1ª Guerra Mundial?", "options": ["1912", "1914", "1918", "1939"], "correct": 1, "explanation": "En 1914"},
    ],
    "i_ar_1": [
        {"question": "حكم النون الساكنة عند الباء؟", "options": ["الإظهار", "الإدغام", "الإقلاب", "الإخفاء"], "correct": 2, "explanation": "الإقلاب"},
    ],
    "i_fr_1": [
        {"question": "Règle du Noun devant Ba ?", "options": ["Izhar", "Idgham", "Iqlab", "Ikhfa"], "correct": 2, "explanation": "Iqlab"},
    ],
    "i_en_1": [
        {"question": "Rule of Noon before Ba?", "options": ["Izhar", "Idgham", "Iqlab", "Ikhfa"], "correct": 2, "explanation": "Iqlab"},
    ],
    "i_es_1": [
        {"question": "¿Regla de Nun ante Ba?", "options": ["Izhar", "Idgham", "Iqlab", "Ikhfa"], "correct": 2, "explanation": "Iqlab"},
    ],
    "p_ar_1": [
        {"question": "وحدة شدة التيار؟", "options": ["الفولط", "الأمبير", "الأوم", "الواط"], "correct": 1, "explanation": "الأمبير"},
    ],
    "p_fr_1": [
        {"question": "Unité de l'intensité ?", "options": ["Volt", "Ampère", "Ohm", "Watt"], "correct": 1, "explanation": "Ampère"},
    ],
    "p_en_1": [
        {"question": "Unit of current?", "options": ["Volt", "Ampere", "Ohm", "Watt"], "correct": 1, "explanation": "Ampere"},
    ],
    "p_es_1": [
        {"question": "¿Unidad de intensidad?", "options": ["Voltio", "Amperio", "Ohmio", "Vatio"], "correct": 1, "explanation": "Amperio"},
    ],
    "s_ar_1": [
        {"question": "الغاز الداخل عند الشهيق؟", "options": ["CO2", "الأكسجين", "الآزوت", "الهيدروجين"], "correct": 1, "explanation": "الأكسجين"},
    ],
    "s_fr_1": [
        {"question": "Gaz entrant à l'inspiration ?", "options": ["CO2", "Oxygène", "Azote", "Hydrogène"], "correct": 1, "explanation": "Oxygène"},
    ],
    "s_en_1": [
        {"question": "Gas entering on inhalation?", "options": ["CO2", "Oxygen", "Nitrogen", "Hydrogen"], "correct": 1, "explanation": "Oxygen"},
    ],
    "s_es_1": [
        {"question": "¿Gas en la inspiración?", "options": ["CO2", "Oxígeno", "Nitrógeno", "Hidrógeno"], "correct": 1, "explanation": "Oxígeno"},
    ],
}

# ----------------------------------------------------------------------------
# إدارة الجلسة
# ----------------------------------------------------------------------------
def init_session_state():
    defaults = {
        "theme": "🌙 Dark",
        "language": "ar",
        "page": "dashboard",
        "selected_subject": None,
        "selected_lesson": None,
        "points": 0,
        "level": 1,
        "student_name": "",
        "quiz_state": {},
        "quiz_finished": False,
        "current_lesson_title": "",
        # Auth
        "authenticated": False,
        "user_role": None,
        "username": None,
        "full_name": None,
        "auth_page": "login",  # login / register
        # Developer panel
        "dev_tab": "lessons",
    }
    for k, v in defaults.items():
        if k not in st.session_state:
            st.session_state[k] = v

init_session_state()

# ----------------------------------------------------------------------------
# الدوال المساعدة
# ----------------------------------------------------------------------------
def T(key):
    lang = st.session_state.language
    return TRANSLATIONS.get(lang, TRANSLATIONS["ar"]).get(key, key)

def get_subject_name(subject_key):
    lang = st.session_state.language
    return SUBJECTS[subject_key].get(lang, SUBJECTS[subject_key]["ar"])

def get_all_lessons(subject, language):
    """يجمع بين الدروس الأساسية والمخصصة."""
    base = LESSONS_DB.get(subject, {}).get(language, [])
    custom = load_custom_lessons()
    custom_list = custom.get(f"{subject}_{language}", [])
    return base + custom_list

def get_all_questions(lesson_id):
    """يجمع بين الأسئلة الأساسية والمخصصة."""
    base = QUESTIONS_DB.get(lesson_id, [])
    custom = load_custom_questions()
    custom_list = custom.get(lesson_id, [])
    return base + custom_list

# ----------------------------------------------------------------------------
# Supabase
# ----------------------------------------------------------------------------
@st.cache_resource(show_spinner=False)
def get_supabase_client():
    if not SUPABASE_AVAILABLE:
        return None
    try:
        url = st.secrets.get("SUPABASE_URL", "")
        key = st.secrets.get("SUPABASE_KEY", "")
        if url and key:
            return create_client(url, key)
    except Exception:
        pass
    return None

supabase = get_supabase_client()

# ----------------------------------------------------------------------------
# نظام النقاط
# ----------------------------------------------------------------------------
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

    st.markdown(f"""
    <style>
        .stApp {{ background-color: {theme['bg']}; color: {theme['text']}; direction: {direction}; }}
        section[data-testid="stSidebar"] {{ background-color: {theme['secondary']}; border-right: 2px solid {theme['border']}; }}
        section[data-testid="stSidebar"] * {{ color: {theme['text']} !important; }}
        .custom-card {{
            background-color: {theme['card']}; color: {theme['text']};
            padding: 20px; border-radius: 12px; border: 1px solid {theme['border']};
            margin-bottom: 15px; box-shadow: 0 4px 12px rgba(0,0,0,0.15);
            transition: transform 0.2s; text-align: {align};
        }}
        .custom-card:hover {{ transform: translateY(-3px); border-color: {theme['accent']}; }}
        h1, h2, h3, h4, h5, h6 {{ color: {theme['text']} !important; text-align: {align}; }}
        p, label, div {{ text-align: {align}; }}
        .stButton > button {{
            background-color: {theme['accent']}; color: white; border-radius: 8px;
            border: none; padding: 10px 20px; font-weight: bold; transition: all 0.2s; width: 100%;
        }}
        .stButton > button:hover {{ opacity: 0.85; transform: scale(1.02); }}
        .stTextInput input, .stSelectbox select, .stTextArea textarea {{
            background-color: {theme['card']} !important; color: {theme['text']} !important;
            border: 1px solid {theme['border']} !important;
        }}
        .stProgress > div > div > div {{ background-color: {theme['accent']}; }}
        div[data-testid="stMetricValue"] {{ color: {theme['accent']} !important; }}
        .main-header {{
            background: linear-gradient(90deg, {theme['accent']}, {theme['secondary']});
            padding: 25px; border-radius: 15px; text-align: center;
            margin-bottom: 25px; box-shadow: 0 6px 20px rgba(0,0,0,0.25);
        }}
        .main-header h1, .main-header p {{ color: white !important; text-align: center; }}
        .main-header h1 {{ margin: 0; font-size: 2.2em; }}
        .main-header p {{ margin: 5px 0 0 0; opacity: 0.9; }}
        .streamlit-expanderHeader {{
            background-color: {theme['card']} !important; color: {theme['text']} !important; border-radius: 8px;
        }}
        details {{ background-color: {theme['card']}; border-radius: 10px; border: 1px solid {theme['border']}; }}
        /* Auth card */
        .auth-card {{
            background-color: {theme['card']}; color: {theme['text']};
            padding: 30px; border-radius: 15px; border: 1px solid {theme['border']};
            box-shadow: 0 8px 25px rgba(0,0,0,0.2); max-width: 500px; margin: 0 auto;
        }}
        .role-badge {{
            display: inline-block; padding: 3px 10px; border-radius: 12px;
            font-size: 0.85em; font-weight: bold; margin-{align}: 5px;
        }}
    </style>
    """, unsafe_allow_html=True)

# ============================================================================
# 🔐 صفحة تسجيل الدخول
# ============================================================================
def render_auth_page():
    apply_theme()

    # زر تغيير اللغة والثيم في الأعلى
    col1, col2, col3 = st.columns([1, 2, 1])
    with col1:
        selected_lang = st.selectbox(
            "🌐", list(LANGUAGES.keys()),
            format_func=lambda k: LANGUAGES[k],
            index=list(LANGUAGES.keys()).index(st.session_state.language),
            label_visibility="collapsed",
            key="auth_lang"
        )
        if selected_lang != st.session_state.language:
            st.session_state.language = selected_lang
            st.rerun()
    with col3:
        selected_theme = st.selectbox(
            "🎨", list(THEMES.keys()),
            index=list(THEMES.keys()).index(st.session_state.theme),
            label_visibility="collapsed",
            key="auth_theme"
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

    # مركز الصفحة
    col1, col2, col3 = st.columns([1, 2, 1])
    with col2:
        # Tabs للتبديل بين الدخول والتسجيل
        tab1, tab2 = st.tabs([T('login'), T('register')])

        with tab1:
            st.markdown(f"#### {T('login')}")
            username = st.text_input(T('username'), key="login_user")
            password = st.text_input(T('password'), type="password", key="login_pass")
            if st.button(T('login_btn'), use_container_width=True, key="login_btn"):
                ok, user = authenticate(username, password)
                if ok:
                    st.session_state.authenticated = True
                    st.session_state.username = username
                    st.session_state.user_role = user["role"]
                    st.session_state.full_name = user.get("full_name", username)
                    st.session_state.student_name = user.get("full_name", username)
                    st.success(T('login_success'))
                    st.rerun()
                else:
                    st.error(T('wrong_creds'))

        with tab2:
            st.markdown(f"#### {T('register')}")
            new_user = st.text_input(T('username'), key="reg_user")
            new_pass = st.text_input(T('password'), type="password", key="reg_pass")
            new_name = st.text_input(T('full_name'), key="reg_name")
            if st.button(T('register_btn'), use_container_width=True, key="reg_btn"):
                ok, msg = register_user(new_user, new_pass, new_name)
                if ok:
                    st.success(msg)
                    st.info("يمكنك الآن تسجيل الدخول من تبويب الدخول")
                else:
                    st.error(msg)

        st.markdown("---")

        # زر الدخول كزائر
        if st.button(f"👤 {T('guest')}", use_container_width=True, key="guest_btn"):
            st.session_state.authenticated = True
            st.session_state.username = "guest"
            st.session_state.user_role = "guest"
            st.session_state.full_name = T('role_guest')
            st.session_state.student_name = T('role_guest')
            st.rerun()

        st.info(T('guest_note'))

    st.markdown("---")
    st.caption("© 2024 3AC RevisioMaroc | حساب المطور الافتراضي: admin / admin123")

# ============================================================================
# 🏠 الصفحة الرئيسية
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
    with c1:
        st.metric(f"🏆 {T('points')}", st.session_state.points)
    with c2:
        st.metric(f"⭐ {T('level')}", st.session_state.level)
    with c3:
        st.metric(f"📚 {T('subjects_count')}", len(SUBJECTS))
    with c4:
        st.metric(f"✅ {T('progress')}", f"{get_progress_percent()}%")

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
# 📚 صفحة الدروس
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

    lessons = get_all_lessons(selected, st.session_state.language)

    if not lessons:
        st.warning(T('no_lessons'))
        return

    for lesson in lessons:
        with st.expander(f"📖 {lesson['title']}", expanded=False):
            st.markdown(lesson['content'])
            st.markdown("---")
            if st.button(T('quiz_lesson'), key=f"quiz_{lesson['id']}", use_container_width=False):
                st.session_state.selected_lesson = lesson['id']
                st.session_state.current_lesson_title = lesson['title']
                st.session_state.page = "quiz"
                st.session_state.quiz_state = {}
                st.session_state.quiz_finished = False
                st.rerun()

# ============================================================================
# 📝 صفحة الاختبارات
# ============================================================================
def render_quiz():
    st.markdown(f"## 📝 {T('smart_quizzes')}")

    if not st.session_state.selected_lesson:
        subject_keys = list(SUBJECTS.keys())
        default_idx = subject_keys.index(st.session_state.selected_subject) if st.session_state.selected_subject else 0
        selected = st.selectbox(
            T('choose_lesson_subject'), subject_keys,
            format_func=lambda k: f"{SUBJECTS[k]['icon']} {get_subject_name(k)}",
            index=default_idx
        )
        st.session_state.selected_subject = selected

        lessons = get_all_lessons(selected, st.session_state.language)
        if not lessons:
            st.warning(T('no_lessons_quiz'))
            return

        lesson_titles = {l['id']: l['title'] for l in lessons}
        lesson_id = st.selectbox(
            T('choose_lesson'),
            list(lesson_titles.keys()),
            format_func=lambda i: lesson_titles[i]
        )

        if st.button(T('start_quiz'), use_container_width=False):
            st.session_state.selected_lesson = lesson_id
            st.session_state.current_lesson_title = lesson_titles[lesson_id]
            st.session_state.quiz_state = {}
            st.session_state.quiz_finished = False
            st.rerun()
        return

    lesson_id = st.session_state.selected_lesson
    questions = get_all_questions(lesson_id)

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
            default = answers.get(i, 0)
            choice = st.radio(
                T('select_answer'),
                options=range(len(options)),
                format_func=lambda j, opts=options: f"{chr(65+j)}. {opts[j]}",
                key=f"q_{i}",
                index=default,
                label_visibility="collapsed"
            )
            answers[i] = choice
            st.markdown("---")

        submitted = st.form_submit_button(T('submit'), use_container_width=True)

        if submitted:
            score = sum(1 for i, q in enumerate(questions) if answers.get(i) == q['correct'])
            st.session_state.quiz_state = {'answers': answers, 'score': score}
            st.session_state.quiz_finished = True
            add_points(score * 10)
            st.rerun()

# ============================================================================
# ⚙️ لوحة تحكم المطور
# ============================================================================
def render_developer_panel():
    st.markdown(f"## ⚙️ {T('developer_panel')}")

    tab1, tab2 = st.tabs([T('manage_lessons'), T('manage_questions')])

    # ------------------------------------------------------------------------
    # Tab 1: إدارة الدروس
    # ------------------------------------------------------------------------
    with tab1:
        st.markdown(f"### {T('add_lesson')}")

        with st.form("add_lesson_form"):
            c1, c2 = st.columns(2)
            with c1:
                subject = st.selectbox(
                    T('lesson_subject'),
                    list(SUBJECTS.keys()),
                    format_func=lambda k: f"{SUBJECTS[k]['icon']} {get_subject_name(k)}",
                    key="dev_lesson_subject"
                )
            with c2:
                language = st.selectbox(
                    T('lesson_language'),
                    list(LANGUAGES.keys()),
                    format_func=lambda k: LANGUAGES[k],
                    key="dev_lesson_lang"
                )

            title = st.text_input(T('lesson_title'), key="dev_lesson_title")
            content = st.text_area(T('lesson_content'), height=200, key="dev_lesson_content")

            if st.form_submit_button(T('save_lesson'), use_container_width=True):
                if title and content:
                    custom = load_custom_lessons()
                    key = f"{subject}_{language}"
                    if key not in custom:
                        custom[key] = []
                    # إنشاء معرّف فريد
                    lesson_id = f"custom_{subject}_{language}_{int(datetime.now().timestamp())}"
                    custom[key].append({
                        "id": lesson_id,
                        "title": title,
                        "content": content
                    })
                    save_custom_lessons(custom)
                    st.success(T('lesson_saved'))
                    st.rerun()
                else:
                    st.error("⚠️ املأ جميع الحقول")

        st.markdown("---")
        st.markdown(f"### {T('manage_lessons')}")

        custom = load_custom_lessons()
        if not custom:
            st.info(T('no_custom_lessons'))
        else:
            for key, lessons_list in list(custom.items()):
                subject, lang = key.rsplit("_", 1) if "_" in key else (key, "ar")
                st.markdown(f"**{get_subject_name(subject) if subject in SUBJECTS else subject} / {LANGUAGES.get(lang, lang)}**")
                for lesson in lessons_list:
                    c1, c2 = st.columns([5, 1])
                    with c1:
                        st.markdown(f"📖 **{lesson['title']}** — `{lesson['id']}`")
                    with c2:
                        if st.button("🗑️", key=f"del_lesson_{lesson['id']}"):
                            custom[key].remove(lesson)
                            if not custom[key]:
                                del custom[key]
                            save_custom_lessons(custom)
                            st.success(T('deleted'))
                            st.rerun()
                st.markdown("---")

    # ------------------------------------------------------------------------
    # Tab 2: إدارة الأسئلة
    # ------------------------------------------------------------------------
    with tab2:
        st.markdown(f"### {T('add_question')}")

        # جلب جميع الدروس المتاحة
        all_available_lessons = {}
        # من القاموس الأساسي
        for subj, langs in LESSONS_DB.items():
            for lang, lessons in langs.items():
                for l in lessons:
                    all_available_lessons[l['id']] = f"[{get_subject_name(subj)} / {LANGUAGES[lang]}] {l['title']}"
        # من المخصصة
        custom_lessons = load_custom_lessons()
        for key, lessons_list in custom_lessons.items():
            parts = key.rsplit("_", 1)
            subj = parts[0] if parts[0] in SUBJECTS else ""
            lang = parts[1] if len(parts) > 1 else "ar"
            for l in lessons_list:
                all_available_lessons[l['id']] = f"[{get_subject_name(subj) if subj else key} / {LANGUAGES.get(lang, lang)}] {l['title']} (مخصص)"

        if not all_available_lessons:
            st.warning("⚠️ لا توجد دروس متاحة لإضافة أسئلة")
        else:
            with st.form("add_question_form"):
                lesson_id = st.selectbox(
                    T('select_lesson_for_question'),
                    list(all_available_lessons.keys()),
                    format_func=lambda i: all_available_lessons[i],
                    key="dev_q_lesson"
                )

                question_text = st.text_area(T('question_text'), key="dev_q_text")
                c1, c2 = st.columns(2)
                with c1:
                    opt_a = st.text_input(T('option_a'), key="dev_q_a")
                    opt_b = st.text_input(T('option_b'), key="dev_q_b")
                with c2:
                    opt_c = st.text_input(T('option_c'), key="dev_q_c")
                    opt_d = st.text_input(T('option_d'), key="dev_q_d")

                correct = st.radio(
                    T('correct_answer'),
                    options=[0, 1, 2, 3],
                    format_func=lambda i: f"{chr(65+i)}",
                    horizontal=True,
                    key="dev_q_correct"
                )
                explanation = st.text_input(T('explanation_text'), key="dev_q_exp")

                if st.form_submit_button(T('save_question'), use_container_width=True):
                    if question_text and opt_a and opt_b and opt_c and opt_d:
                        custom_q = load_custom_questions()
                        if lesson_id not in custom_q:
                            custom_q[lesson_id] = []
                        custom_q[lesson_id].append({
                            "question": question_text,
                            "options": [opt_a, opt_b, opt_c, opt_d],
                            "correct": correct,
                            "explanation": explanation or ""
                        })
                        save_custom_questions(custom_q)
                        st.success(T('question_saved'))
                        st.rerun()
                    else:
                        st.error("⚠️ املأ جميع الحقول")

        st.markdown("---")
        st.markdown(f"### {T('manage_questions')}")

        custom_q = load_custom_questions()
        if not custom_q:
            st.info(T('no_custom_questions'))
        else:
            for lid, qs in list(custom_q.items()):
                lesson_title = all_available_lessons.get(lid, lid)
                st.markdown(f"**📖 {lesson_title}**")
                for idx, q in enumerate(qs):
                    c1, c2 = st.columns([5, 1])
                    with c1:
                        st.markdown(f"❓ {q['question']} — ✅ **{chr(65+q['correct'])}**")
                    with c2:
                        if st.button("🗑️", key=f"del_q_{lid}_{idx}"):
                            custom_q[lid].pop(idx)
                            if not custom_q[lid]:
                                del custom_q[lid]
                            save_custom_questions(custom_q)
                            st.success(T('deleted'))
                            st.rerun()
                st.markdown("---")

# ============================================================================
# 🚀 التوجيه الرئيسي
# ============================================================================

# إذا لم يكن مسجلاً، أظهر صفحة الدخول
if not st.session_state.authenticated:
    render_auth_page()
    st.stop()

# الشريط الجانبي (بعد تسجيل الدخول)
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

    # بطاقة المستخدم
    role = st.session_state.user_role
    role_label = {
        "student": T('role_student'),
        "developer": T('role_developer'),
        "guest": T('role_guest'),
    }.get(role, role)

    badge_color = {"student": "#3498DB", "developer": "#E74C3C", "guest": "#95A5A6"}.get(role, "#4A90E2")

    st.markdown(f"""
    <div class="custom-card" style="text-align:center; padding: 12px;">
        <p style="margin:0; font-size: 0.9em; opacity: 0.7;">{T('logged_as')}</p>
        <p style="margin:5px 0; font-weight: bold;">{st.session_state.full_name or st.session_state.username}</p>
        <span class="role-badge" style="background:{badge_color}; color:white;">{role_label}</span>
    </div>
    """, unsafe_allow_html=True)

    st.markdown("---")

    # اختيار اللغة
    st.markdown(f"### {T('language')}")
    lang_keys = list(LANGUAGES.keys())
    selected_lang = st.selectbox(
        T('choose_language'), lang_keys,
        format_func=lambda k: LANGUAGES[k],
        index=lang_keys.index(st.session_state.language),
        label_visibility="collapsed"
    )
    if selected_lang != st.session_state.language:
        st.session_state.language = selected_lang
        st.rerun()

    # اختيار الثيم
    st.markdown(f"### {T('theme')}")
    theme_keys = list(THEMES.keys())
    selected_theme = st.selectbox(
        T('appearance'), theme_keys,
        index=theme_keys.index(st.session_state.theme),
        label_visibility="collapsed"
    )
    if selected_theme != st.session_state.theme:
        st.session_state.theme = selected_theme
        st.rerun()

    st.markdown("---")

    # القائمة
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

    # لوحة المطور (فقط للمطور)
    if st.session_state.user_role == "developer":
        if st.button(T('developer'), use_container_width=True):
            st.session_state.page = "developer"
            st.rerun()

    st.markdown("---")

    # التقدم (فقط للتلاميذ والزوار)
    if st.session_state.user_role in ["student", "guest"]:
        st.markdown(f"### {T('your_progress')}")
        c1, c2 = st.columns(2)
        with c1:
            st.metric(T('points'), st.session_state.points)
        with c2:
            st.metric(T('level'), st.session_state.level)
        st.progress(get_progress_percent() / 100)
        st.caption(f"{T('level_progress')}: {get_progress_percent()}%")
        st.markdown("---")

    # زر تسجيل الخروج
    if st.button(T('logout'), use_container_width=True):
        for key in ["authenticated", "user_role", "username", "full_name",
                    "points", "level", "student_name", "page", "selected_subject",
                    "selected_lesson", "quiz_state", "quiz_finished"]:
            if key in st.session_state:
                del st.session_state[key]
        st.rerun()

    st.markdown("---")
    st.caption("© 2024 3AC RevisioMaroc")

# التوجيه بين الصفحات
page = st.session_state.page
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