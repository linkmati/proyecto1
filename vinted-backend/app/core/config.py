import os
from dotenv import load_dotenv

# Cargamos las variables del archivo .env para tener las claves de Supabase a mano
load_dotenv()

class Settings:
    SUPABASE_URL: str = os.getenv("SUPABASE_URL")
    SUPABASE_SECRET_KEY: str = os.getenv("SUPABASE_SECRET_KEY")
    DATABASE_URL: str = os.getenv("DATABASE_URL")

settings = Settings()