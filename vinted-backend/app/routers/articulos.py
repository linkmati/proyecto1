from fastapi import APIRouter, Depends, HTTPException
from supabase import Client
from app.db.supabase import get_supabase
from app.models.schemas import ArticuloCreate, ArticuloResponse
from app.core.security import get_current_user

# This creates a grouped router for all item-related endpoints
router = APIRouter(
    prefix="/api/articulos",
    tags=["Articulos"]
)

@router.post("/", response_model=ArticuloResponse)
def create_articulo(
    articulo: ArticuloCreate, 
    db: Client = Depends(get_supabase),
    user_id: str = Depends(get_current_user) # <-- This forces Authentication!
):
    try:
        item_data = articulo.model_dump()
        
        # Automatically set the id_vendedor from the verified JWT!
        item_data["id_vendedor"] = user_id 
        
        response = db.table("articulos").insert(item_data).execute()
        
        if not response.data:
            raise HTTPException(status_code=400, detail="Failed to create item")
            
        return response.data[0]
    
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@router.get("/")
def list_articulos(db: Client = Depends(get_supabase)):
    """
    Fetches all available items.
    """
    try:
        # Fetch items where estado_articulo is 'DISPONIBLE'
        response = db.table("articulos").select("*").eq("estado_articulo", "DISPONIBLE").execute()
        return response.data
    
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))