# ============================================================================
# سكريبت إنشاء حساب المطور — شغّلو مرة وحدة فقط ثم حيّدو
# ============================================================================
import hashlib
from supabase import create_client

URL = "https://mvrdowfzsidxgdczcccrh.supabase.co"
KEY = "eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9.eyJpc3MiOiJzdXBhYmFzZSIsInJlZiI6Im12cmRvd2Z6c2lkeGdkY3pjY3JoIiwicm9sZSI6ImFub24iLCJpYXQiOjE3OTE0Njk0MjIsImV4cCI6MjEwNzA0NTQyMn0.ibu0WZsYyCs7tWUzZkhdjFV8JOTH8U69arR_ObeA_HU"

DEV_USERNAME = "soufianeDEV"
DEV_PASSWORD = "soufiane2030"
DEV_FULLNAME = "Soufiane Ouhazza"

def main():
    print("=" * 60)
    print("🔧 إنشاء حساب المطور")
    print("=" * 60)

    supabase = create_client(URL, KEY)
    password_hash = hashlib.sha256(DEV_PASSWORD.encode()).hexdigest()

    print(f"\n👤 Username: {DEV_USERNAME}")
    print(f"🔒 Password: {DEV_PASSWORD}")
    print(f"🔐 Hash: {password_hash}\n")

    try:
        res = supabase.table("users").select("*").eq("username", DEV_USERNAME).execute()
        if res.data:
            print(f"⚠️ الحساب موجود — كيتم التحديث...")
            supabase.table("users").update({
                "password_hash": password_hash,
                "role": "developer",
                "full_name": DEV_FULLNAME
            }).eq("username", DEV_USERNAME).execute()
            print("✅ تم التحديث")
        else:
            print("📝 كيتم الإنشاء...")
            supabase.table("users").insert({
                "username": DEV_USERNAME,
                "password_hash": password_hash,
                "role": "developer",
                "full_name": DEV_FULLNAME
            }).execute()
            print("✅ تم الإنشاء")

        print("\n" + "=" * 60)
        print("🎉 تنجح! دابا قدر تدخل:")
        print(f"   👤 {DEV_USERNAME}")
        print(f"   🔒 {DEV_PASSWORD}")
        print("=" * 60)

    except Exception as e:
        print(f"\n❌ خطأ: {type(e).__name__} — {e}")

if __name__ == "__main__":
    main()