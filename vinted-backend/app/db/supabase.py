from supabase import create_client, Client
from app.core.config import settings

# Este es el cliente normal, el que obedece las reglas de seguridad (RLS)
supabase_client: Client = create_client(
    settings.SUPABASE_URL, 
    settings.SUPABASE_PUBLISHABLE_KEY
)

# Este es el cliente admin, se salta todas las reglas. ¡Usar con mucho cuidado!
supabase_admin: Client = create_client(
    settings.SUPABASE_URL, 
    settings.SUPABASE_SECRET_KEY
)

# Esto es para que FastAPI pueda pillar el cliente normal cuando lo necesite
def get_supabase() -> Client:
    return supabase_client

# Esto es para pillar el cliente admin (el que manda de verdad)
def get_supabase_admin() -> Client:
    return supabase_admin