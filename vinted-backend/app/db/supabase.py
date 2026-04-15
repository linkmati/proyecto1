from supabase import create_client, Client
from app.core.config import settings

# Standard client (Respects Row Level Security)
supabase_client: Client = create_client(
    settings.SUPABASE_URL, 
    settings.SUPABASE_PUBLISHABLE_KEY
)

# Admin client (Bypasses Row Level Security - use carefully!)
supabase_admin: Client = create_client(
    settings.SUPABASE_URL, 
    settings.SUPABASE_SECRET_KEY
)

# Dependency for standard endpoints
def get_supabase() -> Client:
    return supabase_client

# Dependency for admin/internal endpoints
def get_supabase_admin() -> Client:
    return supabase_admin