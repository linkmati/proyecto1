from fastapi import FastAPI, Depends, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from app.db.supabase import get_db_connection
from app.routers import items, auth, offers, users, messages, favorites, admin

# NOTA PRESENTACIÓN: Inicializamos la app con FastAPI. 
# FastAPI nos genera automáticamente la documentación en /docs.
app = FastAPI(title="Vinted Clone API")

# NOTA PRESENTACIÓN: CORS (Cross-Origin Resource Sharing).
# Esto es imprescindible para que nuestro Frontend (que correrá en otro puerto/dominio)
# pueda hacer peticiones al Backend sin que el navegador bloquee la conexión por seguridad.
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=False,
    allow_methods=["*"],
    allow_headers=["*"],
    expose_headers=["*"]
)

# NOTA PRESENTACIÓN: Separamos el código en "Routers" para que main.py no sea gigante.
# Cada archivo en la carpeta 'routers' tiene sus propias funciones y rutas agrupadas.
app.include_router(auth.router)
app.include_router(users.router)
app.include_router(items.router)
app.include_router(offers.router)
app.include_router(messages.router)
app.include_router(favorites.router)
app.include_router(admin.router)

@app.get("/")
def home():
    return {"message": "API funcionando"}

@app.get("/health")
def salud(conn = Depends(get_db_connection)):
    """Punto de control para ver si la DB responde."""
    # NOTA PRESENTACIÓN: Usamos `Depends` para la inyección de dependencias.
    # FastAPI se encarga de llamar a get_db_connection, pasarnos la conexión, 
    # y cerrarla cuando termina la función.
    try:
        with conn.cursor() as cur:
            cur.execute("SELECT 1")
            res = cur.fetchone()
        return {
            "status": "online",
            "database": "conectada",
            "test_query": res
        }
    except Exception as e:
        # Si llegamos aquí, la conexión existe pero la query falla
        return {"status": "error", "detail": str(e)}
