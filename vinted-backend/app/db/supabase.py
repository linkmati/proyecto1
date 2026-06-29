import psycopg2
from psycopg2.extras import RealDictCursor
from app.core.config import settings
from supabase import create_client, Client

# NOTA PRESENTACIÓN: [SUPABASE_STORAGE] Cliente oficial usado solo para subir y guardar imágenes en Buckets.
supabase_admin: Client = create_client(
    settings.SUPABASE_URL, 
    settings.SUPABASE_SECRET_KEY
)

def get_db_connection():
    """Crea la conexión a la base de datos PostgreSQL con psycopg2."""
    # NOTA PRESENTACIÓN: [DICT_CURSOR] RealDictCursor devuelve las filas como diccionarios en lugar de tuplas.
    conn = psycopg2.connect(settings.DATABASE_URL, cursor_factory=RealDictCursor)
    try:
        # NOTA PRESENTACIÓN: [CONN_GEN] yield mantiene la conexión abierta por petición y asegura el cierre.
        yield conn
    finally:
        conn.close()

def get_supabase_admin() -> Client:
    return supabase_admin

def get_supabase() -> Client:
    return supabase_admin
