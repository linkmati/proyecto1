from fastapi import FastAPI, Depends, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from supabase import Client
from app.db.supabase import get_supabase
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
def health_check(db: Client = Depends(get_supabase)):
    try:
        # Check basic table access
        response = db.table("usuarios").select("id_usuario").limit(1).execute()
        return {
            "status": "online", 
            "database": "connected", 
            "data_check": response.data
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Database connection failed: {str(e)}")