from fastapi import APIRouter, Depends, HTTPException
from app.db.supabase import get_supabase_admin, get_db_connection
from app.models.schemas import UserCreate, TokenResponse
from fastapi.security import OAuth2PasswordRequestForm

router = APIRouter(prefix="/api/auth", tags=["Auth"])

@router.post("/register")
def registro(datos: UserCreate, admin_db = Depends(get_supabase_admin), conn = Depends(get_db_connection)):
    """Paso 1: Alta en Supabase (email/pass). Paso 2: Creamos nuestro perfil en la tabla 'usuarios'."""
    # NOTA PRESENTACIÓN: El registro tiene dos partes separadas para mantener la seguridad.
    try:
        # Parte 1: Delegamos la seguridad (hashear contraseñas, generar tokens) a Supabase Auth.
        # No queremos guardar contraseñas en texto plano nosotros.
        respuesta_auth = admin_db.auth.sign_up({"email": datos.email, "password": datos.password})
        if not respuesta_auth.user: 
            raise HTTPException(status_code=400, detail="No se ha podido crear el usuario")

        uid = respuesta_auth.user.id
        
        # Parte 2: Una vez que Supabase le asigna un ID único seguro (UUID),
        # usamos ESE mismo ID para insertarlo en nuestra propia tabla de usuarios.
        # Así podemos relacionarlo con sus productos, compras, favoritos, etc.
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
        # NOTA PRESENTACIÓN: En vez de un JSON normal, el login usa OAuth2PasswordRequestForm.
        # Esto es un estándar que manda los datos como 'application/x-www-form-urlencoded'.
        
        # Validamos en Supabase
        respuesta_auth = admin_db.auth.sign_in_with_password({"email": formulario.username, "password": formulario.password})
        if not respuesta_auth.user: 
            raise HTTPException(status_code=401, detail="Credenciales incorrectas")

        # NOTA PRESENTACIÓN: Aunque Supabase diga que la contraseña es correcta,
        # nosotros consultamos nuestra base de datos para ver si el usuario está 'suspendido'
        # o expulsado por un administrador, aplicando nuestra propia lógica de negocio.
        with conn.cursor() as cur:
            cur.execute("SELECT estado FROM usuarios WHERE id_usuario = %s", (respuesta_auth.user.id,))
            usuario = cur.fetchone()
            if not usuario: 
                raise HTTPException(status_code=401, detail="El usuario no existe en nuestra DB")
            if usuario["estado"] == "suspendido": 
                raise HTTPException(status_code=403, detail="Tu cuenta está suspendida, habla con el admin")

        # Devolvemos el JWT Token que el frontend usará en cada petición
        return {
            "access_token": respuesta_auth.session.access_token, 
            "token_type": "bearer"
        }
    except Exception as e:
        msg = str(e)
        if "login credentials" in msg: 
            raise HTTPException(status_code=401, detail="Email o contraseña mal escritos")
        raise HTTPException(status_code=401, detail=msg)
