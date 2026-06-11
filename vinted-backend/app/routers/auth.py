from fastapi import APIRouter, Depends, HTTPException
from app.db.supabase import get_supabase_admin, get_db_connection
from app.models.schemas import UserCreate, TokenResponse
from fastapi.security import OAuth2PasswordRequestForm

router = APIRouter(prefix="/api/auth", tags=["Auth"])

@router.post("/register")
def registro(datos: UserCreate, admin_db = Depends(get_supabase_admin), conn = Depends(get_db_connection)):
    """Paso 1: Alta en Supabase (email/pass). Paso 2: Creamos nuestro perfil en la tabla 'usuarios'."""
    try:
        # Alta en el sistema de autenticación (el que gestiona los tokens)
        respuesta_auth = admin_db.auth.sign_up({"email": datos.email, "password": datos.password})
        if not respuesta_auth.user: 
            raise HTTPException(status_code=400, detail="No se ha podido crear el usuario")

        uid = respuesta_auth.user.id
        # Guardamos sus datos básicos en nuestra base de datos con SQL
        with conn.cursor() as cur:
            cur.execute("""
                INSERT INTO usuarios (id_usuario, email, nombre_usuario, estado)
                VALUES (%s, %s, %s, 'activo')
                ON CONFLICT (id_usuario) DO NOTHING
            """, (uid, datos.email, datos.nombre_usuario))
            conn.commit()
        return {"id_usuario": uid, "message": "¡Bienvenido!"}
    except Exception as e:
        conn.rollback()
        raise HTTPException(status_code=400, detail=str(e))

@router.post("/login", response_model=TokenResponse)
def login(formulario: OAuth2PasswordRequestForm = Depends(), admin_db = Depends(get_supabase_admin), conn = Depends(get_db_connection)):
    """Comprobamos email y pass en Supabase y miramos si no está baneado."""
    try:
        # Intentamos entrar con el email (username) y la contraseña
        respuesta_auth = admin_db.auth.sign_in_with_password({"email": formulario.username, "password": formulario.password})
        if not respuesta_auth.user: 
            raise HTTPException(status_code=401, detail="Credenciales incorrectas")

        # Miramos el estado en nuestra tabla 'usuarios' con SQL
        with conn.cursor() as cur:
            cur.execute("SELECT estado FROM usuarios WHERE id_usuario = %s", (respuesta_auth.user.id,))
            usuario = cur.fetchone()
            if not usuario: 
                raise HTTPException(status_code=401, detail="El usuario no existe en nuestra DB")
            if usuario["estado"] == "suspendido": 
                raise HTTPException(status_code=403, detail="Tu cuenta está suspendida, habla con el admin")

        # Si todo ok, devolvemos el token de acceso
        return {
            "access_token": respuesta_auth.session.access_token, 
            "token_type": "bearer"
        }
    except Exception as e:
        msg = str(e)
        if "login credentials" in msg: 
            raise HTTPException(status_code=401, detail="Email o contraseña mal escritos")
        raise HTTPException(status_code=401, detail=msg)
