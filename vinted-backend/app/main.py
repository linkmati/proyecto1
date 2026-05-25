from fastapi import FastAPI, Depends, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from supabase import Client
from app.db.supabase import get_supabase, get_supabase_admin
from app.routers import items, auth, offers, users, messages, favorites, admin

app = FastAPI(title="Vinted Clone API")

# Aquí configuramos el CORS para que la web pueda hablar con el servidor sin que el navegador nos bloquee
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=False,
    allow_methods=["*"],
    allow_headers=["*"],
    expose_headers=["*"]
)

# Metemos todos los archivos de rutas para que el servidor sepa qué hacer cuando entramos en /api/...
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
def health_check(
    db: Client = Depends(get_supabase),
    admin_db: Client = Depends(get_supabase_admin)
):
    # Esto es solo para ver si el servidor y la base de datos están vivos
    results = {"status": "online"}
    
    try:
        # Probamos si la base de datos normal responde
        db.table("usuarios").select("id_usuario").limit(1).execute()
        results["database_rls"] = "connected"
    except Exception as e:
        results["database_rls"] = f"error (seguro que es por el RLS): {str(e)}"
        
    try:
        # Probamos con el admin, que se salta todas las reglas de seguridad
        admin_db.table("usuarios").select("id_usuario").limit(1).execute()
        results["database_admin"] = "connected"
    except Exception as e:
        results["database_admin"] = f"error: {str(e)}"
        
    return results