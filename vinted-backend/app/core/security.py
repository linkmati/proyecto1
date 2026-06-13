from fastapi import Depends, HTTPException
from fastapi.security import OAuth2PasswordBearer
from supabase import Client
from app.db.supabase import get_supabase, get_supabase_admin, get_db_connection

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

def get_admin_user(
    token: str = Depends(oauth2_scheme), 
    db: Client = Depends(get_supabase_admin),
    conn = Depends(get_db_connection)
):
    """
    Comprueba si el usuario es un administrador de verdad.
    """
    user_id = get_current_user(token, db)
    
    cursor = conn.cursor()
    query = "SELECT rol FROM usuarios WHERE id_usuario = %s"
    cursor.execute(query, (user_id,))
    row = cursor.fetchone()
    cursor.close()
    
    if not row:
        raise HTTPException(status_code=403, detail="Admin privileges required: Profile not found")
        
    role = row.get("rol")
    if role != "admin":
        # Si no eres admin, pues no te dejamos pasar
        raise HTTPException(status_code=403, detail="Admin privileges required")
        
    return user_id
