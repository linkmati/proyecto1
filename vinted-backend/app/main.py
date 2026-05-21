from fastapi import FastAPI, Depends, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from supabase import Client
from app.db.supabase import get_supabase, get_supabase_admin
from app.routers import items, auth, offers, users, messages, favorites, admin

app = FastAPI(title="Vinted Clone API")

# Configure CORS - Broad policy for local network/dev access
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=False,
    allow_methods=["*"],
    allow_headers=["*"],
    expose_headers=["*"]
)

# Connect the routers to the app
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
    results = {"status": "online"}
    
    try:
        # Check regular client (subject to RLS)
        db.table("usuarios").select("id_usuario").limit(1).execute()
        results["database_rls"] = "connected"
    except Exception as e:
        results["database_rls"] = f"error (likely RLS): {str(e)}"
        
    try:
        # Check admin client (bypasses RLS)
        admin_db.table("usuarios").select("id_usuario").limit(1).execute()
        results["database_admin"] = "connected"
    except Exception as e:
        results["database_admin"] = f"error: {str(e)}"
        
    return results