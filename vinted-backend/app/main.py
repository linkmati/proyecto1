from fastapi import FastAPI, Depends, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from app.db.supabase import get_db_connection
from app.routers import items, auth, offers, users, messages, favorites, admin

# NOTA PRESENTACIÓN: [API_INIT] Inicialización principal del framework FastAPI.
app = FastAPI(title="Vinted Clone API")

# NOTA PRESENTACIÓN: [CORS_POLICY] Middleware para habilitar CORS y permitir llamadas desde el frontend.
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=False,
    allow_methods=["*"],
    allow_headers=["*"],
    expose_headers=["*"]
)

# NOTA PRESENTACIÓN: [MODULAR_ROUTING] Inclusión de submódulos de rutas para desacoplar controladores.
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
    try:
        cursor = conn.cursor()
        query = "SELECT 1"
        cursor.execute(query)
        res = cursor.fetchone()
        cursor.close()
        
        return {
            "status": "online",
            "database": "conectada",
            "test_query": res
        }
    except Exception as e:
        return {"status": "error", "detail": str(e)}
