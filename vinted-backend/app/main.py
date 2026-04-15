from fastapi import FastAPI, Depends, HTTPException
from supabase import Client
from app.db.supabase import get_supabase
from app.routers import articulos, auth, ofertas



app = FastAPI(title="Vinted Clone API")

# Connect the router to the app
app.include_router(auth.router)
app.include_router(articulos.router)
app.include_router(ofertas.router)

@app.get("/")
def read_root():
    return {"message": "Welcome to the Marketplace API"}

@app.get("/health")
def health_check(db: Client = Depends(get_supabase)):
    try:
        response = db.table("usuarios").select("id_usuario").limit(1).execute()
        return {
            "status": "online", 
            "database": "connected", 
            "data_check": response.data
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Database connection failed: {str(e)}")