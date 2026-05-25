from fastapi import APIRouter, Depends, HTTPException
from fastapi.security import OAuth2PasswordRequestForm
from supabase import Client
from app.db.supabase import get_supabase, get_supabase_admin
from app.models.schemas import UserCreate, TokenResponse

# Usamos "Auth" para que en la web de documentación (Swagger) salga todo juntito
router = APIRouter(prefix="/api/auth", tags=["Auth"])

@router.post("/register")
def register_user(
    user_data: UserCreate, 
    db: Client = Depends(get_supabase),
    admin_db: Client = Depends(get_supabase_admin)
):
    """
    Aquí es donde se apunta la gente nueva. 
    Primero crea el usuario en Supabase (lo de la contraseña y eso) y luego lo guardamos en nuestra tabla de usuarios.
    """
    try:
        # Paso 1: Intentamos registrar al usuario en Supabase
        # Esto guarda el email y la pass de forma segura
        auth_response = db.auth.sign_up({
            "email": user_data.email,
            "password": user_data.password
        })
        
        # Si Supabase no nos devuelve un usuario, es que algo ha fallado
        if not auth_response.user:
            raise HTTPException(
                status_code=400, 
                detail="Registration failed. Check if email is valid or already exists."
            )

        new_user_id = auth_response.user.id

        # Paso 2: Guardamos los datos en nuestra propia tabla 'usuarios'
        # Usamos 'admin_db' porque así nos saltamos las reglas de seguridad y nos deja crear el perfil
        admin_db.table("usuarios").upsert({
            "id_usuario": new_user_id,
            "email": user_data.email,
            "nombre_usuario": user_data.nombre_usuario,
            "estado": "activo"
        }).execute()
        
        return {
            "message": "User registered successfully!", 
            "id_usuario": new_user_id
        }
        
    except Exception as error:
        # Imprimimos el error por consola por si tenemos que debugear y le mandamos algo al usuario
        print(f"DEBUG - Registration Error: {str(error)}")
        
        # Si ya es un error de los nuestros (HTTPException), lo soltamos tal cual
        if isinstance(error, HTTPException):
            raise error
            
        # Para cualquier otra cosa rara, soltamos un error 400
        raise HTTPException(status_code=400, detail=str(error))

@router.post("/login", response_model=TokenResponse)
def login_user(
    form_data: OAuth2PasswordRequestForm = Depends(), 
    db: Client = Depends(get_supabase),
    admin_db: Client = Depends(get_supabase_admin)
):
    """
    Para entrar en la cuenta. Nos da un token que es como el carnet para hacer cosas luego.
    El formulario este de FastAPI pide 'username' (que es el email) y 'password'.
    """
    try:
        # Paso 1: Entrar con el email y la pass
        auth_response = db.auth.sign_in_with_password({
            "email": form_data.username, 
            "password": form_data.password
        })
        
        if not auth_response.user:
            raise HTTPException(status_code=401, detail="Invalid email or password.")

        # Paso 2: Miramos si el usuario de verdad existe en nuestra tabla
        # Si no está ahí, es que algo raro ha pasado o lo han borrado.
        profile_res = admin_db.table("usuarios").select("*").eq("id_usuario", auth_response.user.id).execute()
        
        if not profile_res.data:
            raise HTTPException(
                status_code=401, 
                detail="Tu cuenta ya no existe en nuestra base de datos. Por favor, regístrate de nuevo."
            )
            
        if profile_res.data[0].get("estado") == "suspendido":
            raise HTTPException(
                status_code=403, 
                detail="Tu cuenta ha sido suspendida. Contacta con soporte para más información."
            )

        # Actualizamos el email por si acaso
        admin_db.table("usuarios").update({
            "email": auth_response.user.email
        }).eq("id_usuario", auth_response.user.id).execute()
        
        # Paso 3: Devolvemos el token que se usará para las demás peticiones
        return {
            "access_token": auth_response.session.access_token, 
            "token_type": "bearer"
        }
        
    except Exception as error:
        print(f"DEBUG - Login Error: {str(error)}")
        # Si el error viene de Supabase Auth, intentamos pasar el mensaje real
        error_msg = str(error)
        if "Invalid login credentials" in error_msg:
            raise HTTPException(status_code=401, detail="Email o contraseña incorrectos.")
        
        raise HTTPException(status_code=401, detail=f"Error en la autenticación: {error_msg}")
