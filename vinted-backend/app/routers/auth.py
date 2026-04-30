from fastapi import APIRouter, Depends, HTTPException
from fastapi.security import OAuth2PasswordRequestForm
from supabase import Client
from app.db.supabase import get_supabase, get_supabase_admin
from app.models.schemas import UsuarioCreate, TokenResponse

router = APIRouter(prefix="/api/auth", tags=["Auth"])

@router.post("/register")
def register_user(
    user: UsuarioCreate, 
    db: Client = Depends(get_supabase),
    admin_db: Client = Depends(get_supabase_admin)
):
    try:
        print(f"DEBUG: Registering {user.email}")
        
        # 1. Intentar registrar en Supabase Auth
        user_id = None
        try:
            auth_res = db.auth.sign_up({
                "email": user.email,
                "password": user.password
            })
            if auth_res.user:
                user_id = auth_res.user.id
        except Exception as auth_err:
            error_str = str(auth_err).lower()
            if "already registered" in error_str:
                # Si ya existe, intentamos recuperar el ID via admin si es posible
                # o pedimos login. Por seguridad, Supabase no suele dar el ID en el error.
                raise HTTPException(status_code=400, detail="User already registered. Please login.")
            raise auth_err
        
        if not user_id:
            # Si no hay ID pero no dio error, puede que requiera confirmación de email activa
            # En ese caso, el usuario se crea en Auth pero no se devuelve sesión.
            # Intentamos buscarlo via admin para sincronizar la tabla 'usuarios'
            search = admin_db.table("usuarios").select("id_usuario").eq("email", user.email).execute()
            if search.data:
                return {"message": "User exists and synced", "id_usuario": search.data[0]["id_usuario"]}
            
            raise HTTPException(status_code=400, detail="Registration pending email confirmation or failed.")

        # 2. Sincronizar con tabla 'usuarios' usando admin_db (bypass RLS)
        admin_db.table("usuarios").upsert({
            "id_usuario": user_id,
            "email": user.email,
            "estado": "activo"
        }).execute()
        
        return {"message": "User registered successfully", "id_usuario": user_id}
        
    except Exception as e:
        print(f"ERROR Register: {str(e)}")
        if isinstance(e, HTTPException): raise e
        raise HTTPException(status_code=400, detail=str(e))

@router.post("/login", response_model=TokenResponse)
def login_user(
    form_data: OAuth2PasswordRequestForm = Depends(), 
    db: Client = Depends(get_supabase),
    admin_db: Client = Depends(get_supabase_admin)
):
    try:
        # 1. Sign in
        auth_res = db.auth.sign_in_with_password({
            "email": form_data.username, 
            "password": form_data.password
        })
        
        if not auth_res.user:
            raise HTTPException(status_code=401, detail="Login failed")

        # 2. Asegurar sincronización de perfil
        admin_db.table("usuarios").upsert({
            "id_usuario": auth_res.user.id,
            "email": auth_res.user.email,
            "estado": "activo"
        }).execute()
        
        return {
            "access_token": auth_res.session.access_token, 
            "token_type": "bearer"
        }
    except Exception as e:
        print(f"ERROR Login: {str(e)}")
        raise HTTPException(status_code=401, detail="Invalid credentials or unconfirmed email")