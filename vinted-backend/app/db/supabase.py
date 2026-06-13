import psycopg2
from psycopg2.extras import RealDictCursor
from app.core.config import settings
from supabase import create_client, Client

# Cliente Supabase para Storage (las fotos siguen yendo por aquí)
supabase_admin: Client = create_client(
    settings.SUPABASE_URL, 
    settings.SUPABASE_SECRET_KEY
)

def get_db_connection():
    """Crea la conexión a la base de datos PostgreSQL con psycopg2."""
    conn = psycopg2.connect(settings.DATABASE_URL, cursor_factory=RealDictCursor)
    try:
        yield conn
    finally:
        conn.close()

def get_supabase_admin() -> Client:
    return supabase_admin

def get_supabase() -> Client:
    return supabase_admin
