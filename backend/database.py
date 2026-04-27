import os
from dotenv import load_dotenv
from supabase import create_client, Client
from functools import lru_cache

# 1. Load Environment Variables
# This reads the .env file in your /backend folder
load_dotenv()

class DatabaseConfig:
    """Configuration class to validate Supabase credentials."""
    URL: str = os.getenv("SUPABASE_URL")
    SERVICE_KEY: str = os.getenv("SUPABASE_SERVICE_KEY")

    @classmethod
    def validate(cls):
        if not cls.URL or not cls.SERVICE_KEY:
            raise ValueError(
                "❌ MISSING CREDENTIALS: Set SUPABASE_URL and SUPABASE_SERVICE_KEY in your .env file."
            )

# 2. Singleton Supabase Client
# Using @lru_cache ensures we only create the client ONCE, saving memory.
@lru_cache()
def get_supabase() -> Client:
    """
    Initializes and returns a Supabase Client.
    Uses the SERVICE_ROLE_KEY to allow the backend to bypass RLS 
    for administrative tasks like order processing.
    """
    DatabaseConfig.validate()
    
    try:
        client: Client = create_client(
            DatabaseConfig.URL, 
            DatabaseConfig.SERVICE_KEY
        )
        return client
    except Exception as e:
        print(f"❌ Failed to connect to Supabase: {str(e)}")
        raise

# 3. Create a global instance for easy import
supabase = get_supabase()

# 4. Helper Test Function
def test_connection():
    """Quick check to see if we can reach the products table."""
    try:
        response = supabase.table("products").select("count", count="exact").limit(1).execute()
        print("✅ Supabase Connection Successful!")
        return True
    except Exception:
        print("⚠️ Supabase connected, but failed to read 'products' table. Check your SQL setup.")
        return False

if __name__ == "__main__":
    # This runs ONLY if you execute 'python database.py' directly
    test_connection()