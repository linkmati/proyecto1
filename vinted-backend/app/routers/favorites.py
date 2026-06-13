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
        cursor = conn.cursor()
        query = """
            SELECT a.* 
            FROM articulos a
            JOIN favoritos f ON a.id_articulo = f.id_articulo
            WHERE f.id_usuario = %s
        """
        cursor.execute(query, (user_id,))
        items = cursor.fetchall()
        
        for item in items:
            query_fotos = "SELECT * FROM fotos_articulo WHERE id_articulo = %s"
            cursor.execute(query_fotos, (item["id_articulo"],))
            item["fotos"] = cursor.fetchall()
            
        cursor.close()
        return items
        
    except Exception as e:
        raise HTTPException(status_code=500, detail="Could not fetch favorites")

@router.post("/{item_id}")
def add_to_favorites(
    item_id: int,
    conn = Depends(get_db_connection),
    user_id: str = Depends(get_current_user)
):
    try:
        cursor = conn.cursor()
        query = """
            INSERT INTO favoritos (id_usuario, id_articulo) 
            VALUES (%s, %s)
            ON CONFLICT (id_usuario, id_articulo) DO NOTHING
        """
        cursor.execute(query, (user_id, item_id))
        conn.commit()
        cursor.close()
        
        return {"status": "success", "message": "Artículo añadido a favoritos"}
        
    except Exception as e:
        conn.rollback()
        raise HTTPException(status_code=500, detail="Could not add to favorites")

@router.delete("/{item_id}")
def remove_from_favorites(
    item_id: int,
    conn = Depends(get_db_connection),
    user_id: str = Depends(get_current_user)
):
    try:
        cursor = conn.cursor()
        query = "DELETE FROM favoritos WHERE id_usuario = %s AND id_articulo = %s"
        cursor.execute(query, (user_id, item_id))
        conn.commit()
        cursor.close()
            
        return {"status": "success", "message": "Item removed from favorites"}
        
    except Exception as e:
        conn.rollback()
        raise HTTPException(status_code=500, detail="Could not remove favorite")
