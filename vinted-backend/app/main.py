from fastapi import FastAPI, Depends, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from supabase import Client
from app.db.supabase import get_supabase_admin, get_db_connection
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

app.include_router(auth.router)
app.include_router(users.router)
app.include_router(items.router)
app.include_router(offers.router)
app.include_router(messages.router)
app.include_router(favorites.router)
app.include_router(admin.router)

@app.get("/")
def read_root():
    return {"message": "Welcome to the Marketplace API"}

@app.get("/health")
def health_check(conn = Depends(get_db_connection)):
    results = {"status": "online"}
    
    try:
        with conn.cursor() as cur:
            cur.execute("SELECT id_usuario FROM usuarios LIMIT 1")
            cur.fetchone()
        results["database"] = "connected (SQL empotrado)"
    except Exception as e:
        results["database"] = f"error: {str(e)}"
        
    return results