from fastapi import FastAPI, Depends, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from app.db.supabase import get_db_connection
from app.routers import items, auth, offers, users, messages, favorites, admin

app = FastAPI(title="Vinted Clone API")

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=False,
    allow_methods=["*"],
    allow_headers=["*"],
    expose_headers=["*"]
)

# Registramos las rutas
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
