import os
from dotenv import load_dotenv

# Load variables from the .env file
load_dotenv()

class Settings:
    SUPABASE_URL: str = os.getenv("SUPABASE_URL")
    SUPABASE_PUBLISHABLE_KEY: str = os.getenv("SUPABASE_PUBLISHABLE_KEY")
    SUPABASE_SECRET_KEY: str = os.getenv("SUPABASE_SECRET_KEY")

settings = Settings()