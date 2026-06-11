import psycopg2
from psycopg2.extras import RealDictCursor
from app.core.config import settings
from supabase import create_client, Client

# Mantenemos los clientes de Supabase SOLO para el storage (subir imágenes)
# y tal vez algo de Auth si no migramos TODO el auth.
supabase_admin: Client = create_client(
    settings.SUPABASE_URL, 
    settings.SUPABASE_SECRET_KEY
)

def get_db_connection():
    """
    Crea una conexión a la base de datos PostgreSQL mediante psycopg2.
    """
    conn = psycopg2.connect(settings.DATABASE_URL, cursor_factory=RealDictCursor)
    try:
        yield conn
    finally:
        conn.close()

def get_supabase_admin() -> Client:
    """
    Se mantiene para el storage (subir imágenes).
    """
    return supabase_admin

# Alias temporal por si algún router sigue usando get_supabase para auth/storage
def get_supabase() -> Client:
    return supabase_admin
