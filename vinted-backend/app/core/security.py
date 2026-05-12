from fastapi import Depends, HTTPException
from fastapi.security import OAuth2PasswordBearer
from supabase import Client
from app.db.supabase import get_supabase

# This tells FastAPI where the login endpoint is for the Swagger UI
oauth2_scheme = OAuth2PasswordBearer(tokenUrl="/api/auth/login")

def get_current_user(token: str = Depends(oauth2_scheme), db: Client = Depends(get_supabase)):
    """
    Validates the JWT token and returns the authenticated user's ID.
    """
    try:
        # Ask Supabase to verify the token
        user_res = db.auth.get_user(token)
        if not user_res.user:
            raise HTTPException(status_code=401, detail="Invalid authentication credentials")
        
        # Return the verified user ID
        return user_res.user.id
    
    except Exception:
        raise HTTPException(status_code=401, detail="Invalid or expired token")

def get_admin_user(token: str = Depends(oauth2_scheme), db: Client = Depends(get_supabase)):
    """
    Verifies the user is an admin.
    """
    user_id = get_current_user(token, db)
    
    # Check role in the database
    response = db.table("usuarios").select("rol").eq("id_usuario", user_id).execute()
    
    if not response.data or response.data[0].get("rol") != "admin":
        raise HTTPException(status_code=403, detail="Admin privileges required")
        
    return user_id