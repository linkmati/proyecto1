import psycopg2
from psycopg2.extras import RealDictCursor
from app.core.config import settings
from supabase import create_client, Client

# NOTA PRESENTACIÓN: Mantuvimos el cliente de Supabase oficial SOLO para Storage.
# Enviar imágenes a través de base de datos es ineficiente, así que
# usamos el SDK de Supabase para guardarlas en sus "Buckets" y luego
# solo guardamos la URL pública (un string) en nuestra base de datos.
supabase_admin: Client = create_client(
    settings.SUPABASE_URL, 
    settings.SUPABASE_SECRET_KEY
)

def get_db_connection():
    """Crea la conexión a la base de datos PostgreSQL con psycopg2."""
    # NOTA PRESENTACIÓN: Usamos `RealDictCursor`. Por defecto, psycopg2 devuelve las filas 
    # como tuplas (ej: (1, 'zapato', 15.5)). RealDictCursor las devuelve como diccionarios
    # (ej: {"id": 1, "nombre": "zapato", "precio": 15.5}), que es justo lo que FastAPI
    # necesita para convertirlas fácilmente a JSON.
    conn = psycopg2.connect(settings.DATABASE_URL, cursor_factory=RealDictCursor)
    try:
        # NOTA PRESENTACIÓN: Usar `yield` convierte esta función en un generador.
        # Sirve para que la conexión permanezca abierta mientras dura la petición
        # y se asegure de cerrarse en el bloque `finally` pase lo que pase.
        yield conn
    finally:
        conn.close()

def get_supabase_admin() -> Client:
    return supabase_admin

def get_supabase() -> Client:
    return supabase_admin
