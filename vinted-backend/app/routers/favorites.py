from fastapi import APIRouter, Depends, HTTPException
from supabase import Client
from typing import List, Dict
from app.db.supabase import get_supabase, get_supabase_admin
from app.core.security import get_current_user
from app.models.schemas import ItemResponse

router = APIRouter(prefix="/api/favorites", tags=["Favorites"])

@router.get("", response_model=List[ItemResponse])
def list_my_favorites(
    admin_db: Client = Depends(get_supabase_admin),
    user_id: str = Depends(get_current_user)
):
    """
    Saca una lista con todos los productos que has guardado como favoritos.
    Viene con las fotos y todo el detalle.
    """
    try:
        # Usamos el admin_db para que nos deje juntar las tablas sin dar errores de permisos
        response = admin_db.table("favoritos") \
            .select("*, articulos(*, fotos:fotos_articulo(*))") \
            .eq("id_usuario", user_id) \
            .execute()
            
        # Limpiamos un poco lo que nos devuelve la base de datos para que solo salgan los productos
        return [fav["articulos"] for fav in response.data if fav.get("articulos")]
        
    except Exception as e:
        print(f"DEBUG - Favorite List Error: {str(e)}")
        raise HTTPException(status_code=500, detail="Could not fetch favorites")

@router.post("/{item_id}")
def add_to_favorites(
    item_id: int,
    admin_db: Client = Depends(get_supabase_admin),
    user_id: str = Depends(get_current_user)
):
    """
    Para guardar un producto en favoritos. 
    Si ya lo tenías, pues no pasa nada, lo vuelve a guardar encima.
    """
    try:
        admin_db.table("favoritos").upsert({
            "id_usuario": user_id,
            "id_articulo": item_id
        }).execute()
        
        return {"status": "success", "message": "Item added to favorites"}
        
    except Exception as e:
        print(f"DEBUG - Add Favorite Error: {str(e)}")
        raise HTTPException(status_code=500, detail="Could not add to favorites")

@router.delete("/{item_id}")
def remove_from_favorites(
    item_id: int,
    admin_db: Client = Depends(get_supabase_admin),
    user_id: str = Depends(get_current_user)
):
    """
    Para quitar un producto de tu lista de favoritos.
    """
    try:
        admin_db.table("favoritos") \
            .delete() \
            .eq("id_usuario", user_id) \
            .eq("id_articulo", item_id) \
            .execute()
            
        return {"status": "success", "message": "Item removed from favorites"}
        
    except Exception as e:
        print(f"DEBUG - Remove Favorite Error: {str(e)}")
        raise HTTPException(status_code=500, detail="Could not remove favorite")
