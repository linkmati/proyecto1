from fastapi import APIRouter, Depends, HTTPException
from typing import List
from app.db.supabase import get_db_connection
from app.core.security import get_current_user
from app.models.schemas import ItemResponse

router = APIRouter(prefix="/api/favorites", tags=["Favorites"])

@router.get("", response_model=List[ItemResponse])
def list_my_favorites(
    conn = Depends(get_db_connection),
    user_id: str = Depends(get_current_user)
):
    try:
        with conn.cursor() as cur:
            cur.execute("""
                SELECT a.* 
                FROM articulos a
                JOIN favoritos f ON a.id_articulo = f.id_articulo
                WHERE f.id_usuario = %s
            """, (user_id,))
            items = cur.fetchall()
            
            for item in items:
                cur.execute("SELECT * FROM fotos_articulo WHERE id_articulo = %s", (item["id_articulo"],))
                item["fotos"] = cur.fetchall()
                
        return items
        
    except Exception as e:
        print(f"DEBUG - Favorite List Error: {str(e)}")
        raise HTTPException(status_code=500, detail="Could not fetch favorites")

@router.post("/{item_id}")
def add_to_favorites(
    item_id: int,
    conn = Depends(get_db_connection),
    user_id: str = Depends(get_current_user)
):
    try:
        with conn.cursor() as cur:
            cur.execute("""
                INSERT INTO favoritos (id_usuario, id_articulo) 
                VALUES (%s, %s)
                ON CONFLICT (id_usuario, id_articulo) DO NOTHING
            """, (user_id, item_id))
            conn.commit()
        
        return {"status": "success", "message": "Artículo añadido a favoritos"}
        
    except Exception as e:
        conn.rollback()
        print(f"DEBUG - Add Favorite Error: {str(e)}")
        raise HTTPException(status_code=500, detail="Could not add to favorites")

@router.delete("/{item_id}")
def remove_from_favorites(
    item_id: int,
    conn = Depends(get_db_connection),
    user_id: str = Depends(get_current_user)
):
    try:
        with conn.cursor() as cur:
            cur.execute("DELETE FROM favoritos WHERE id_usuario = %s AND id_articulo = %s", (user_id, item_id))
            conn.commit()
            
        return {"status": "success", "message": "Item removed from favorites"}
        
    except Exception as e:
        conn.rollback()
        print(f"DEBUG - Remove Favorite Error: {str(e)}")
        raise HTTPException(status_code=500, detail="Could not remove favorite")