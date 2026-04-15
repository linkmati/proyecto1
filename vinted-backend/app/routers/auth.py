from fastapi import APIRouter, Depends, HTTPException
from fastapi.security import OAuth2PasswordRequestForm
from supabase import Client
from app.db.supabase import get_supabase
from app.models.schemas import UsuarioCreate, TokenResponse

router = APIRouter(prefix="/api/auth", tags=["Auth"])

@router.post("/register")
def register_user(user: UsuarioCreate, db: Client = Depends(get_supabase)):
    try:
        # 1. Sign up the user securely via Supabase Auth
        auth_res = db.auth.sign_up({
            "email": user.email,
            "password": user.password
        })
        
        # 2. Sync the user to your custom 'usuarios' table using the same UUID
        user_id = auth_res.user.id
        db.table("usuarios").insert({
            "id_usuario": user_id,
            "email": user.email,
            "estado": "ACTIVO"
            # Notice we skip 'contrasena' to let Supabase handle security!
        }).execute()
        
        return {"message": "User registered successfully", "id_usuario": user_id}
        
    except Exception as e:
        raise HTTPException(status_code=400, detail=str(e))

@router.post("/login", response_model=TokenResponse)
def login_user(form_data: OAuth2PasswordRequestForm = Depends(), db: Client = Depends(get_supabase)):
    try:
        # FastAPI's form_data uses 'username' even if we expect an email
        auth_res = db.auth.sign_in_with_password({
            "email": form_data.username, 
            "password": form_data.password
        })
        
        # Return the JWT token Supabase gives us
        return {
            "access_token": auth_res.session.access_token, 
            "token_type": "bearer"
        }
    except Exception as e:
        raise HTTPException(status_code=401, detail="Incorrect email or password")