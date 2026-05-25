from fastapi import Depends, HTTPException
from fastapi.security import OAuth2PasswordBearer
from supabase import Client
from app.db.supabase import get_supabase, get_supabase_admin

# Esto le dice a FastAPI dónde tiene que ir para loguearse en el Swagger
oauth2_scheme = OAuth2PasswordBearer(tokenUrl="/api/auth/login")

def get_current_user(token: str = Depends(oauth2_scheme), db: Client = Depends(get_supabase)):
    """
    Mira si el token es válido y te dice qué usuario es el que está haciendo la petición.
    """
    try:
        # Le preguntamos a Supabase si el token este de mentira es verdad
        user_res = db.auth.get_user(token)
        if not user_res.user:
            raise HTTPException(status_code=401, detail="Invalid authentication credentials")
        
        # Si todo va bien, devolvemos el ID del usuario verificado
        return user_res.user.id
    
    except Exception:
        raise HTTPException(status_code=401, detail="Invalid or expired token")

def get_admin_user(token: str = Depends(oauth2_scheme), db: Client = Depends(get_supabase_admin)):
    """
    Comprueba si el usuario es un administrador de verdad.
    """
    user_id = get_current_user(token, db)
    
    # Miramos en la tabla de usuarios qué rol tiene
    response = db.table("usuarios").select("rol").eq("id_usuario", user_id).execute()
    
    if not response.data:
        print(f"DEBUG - get_admin_user: No profile found for user_id {user_id}")
        raise HTTPException(status_code=403, detail="Admin privileges required: Profile not found")
        
    role = response.data[0].get("rol")
    if role != "admin":
        # Si no eres admin, pues no te dejamos pasar
        print(f"DEBUG - get_admin_user: User {user_id} has role '{role}', not 'admin'")
        raise HTTPException(status_code=403, detail="Admin privileges required")
        
    return user_id