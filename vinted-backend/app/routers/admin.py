from fastapi import APIRouter, Depends, HTTPException
from typing import List, Optional
from app.db.supabase import get_db_connection
from app.core.security import get_admin_user
from app.models.schemas import ItemResponse, UserResponse, OfferResponse, ItemUpdate

router = APIRouter(prefix="/api/admin", tags=["Admin"])

@router.get("/items", response_model=List[ItemResponse])
def get_items(conn = Depends(get_db_connection), admin_id: str = Depends(get_admin_user), search: Optional[str] = None):
    """Lista todos los artículos del sistema."""
    query = """
        SELECT a.*, u.nombre_usuario, u.email
        FROM articulos a
        LEFT JOIN usuarios u ON a.id_vendedor = u.id_usuario
    """
    params = []
    if search:
        query += " WHERE LOWER(a.titulo) LIKE LOWER(%s)"
        params.append(f"%{search}%")
    query += " ORDER BY a.created_at DESC"
    
    cursor = conn.cursor()
    cursor.execute(query, tuple(params))
    items = cursor.fetchall()
    
    for i in items:
        query_fotos = "SELECT * FROM fotos_articulo WHERE id_articulo = %s"
        cursor.execute(query_fotos, (i["id_articulo"],))
        i["fotos"] = cursor.fetchall()
        i["vendedor_nombre"] = i["nombre_usuario"] or i["email"].split("@")[0]
        
    cursor.close()
    return items

@router.delete("/items/{id}")
def delete_item(id: int, conn = Depends(get_db_connection), admin_id: str = Depends(get_admin_user)):
    """Eliminación forzosa por admin."""
    cursor = conn.cursor()
    query = "DELETE FROM articulos WHERE id_articulo = %s"
    cursor.execute(query, (id,))
    conn.commit()
    cursor.close()
    return {"status": "deleted"}

@router.get("/users", response_model=List[UserResponse])
def get_users(conn = Depends(get_db_connection), admin_id: str = Depends(get_admin_user)):
    """Lista todos los usuarios."""
    cursor = conn.cursor()
    query = "SELECT * FROM usuarios ORDER BY created_at DESC"
    cursor.execute(query)
    users = cursor.fetchall()
    cursor.close()
    return users

@router.patch("/users/{id}/suspend")
def suspend_user(id: str, conn = Depends(get_db_connection), admin_id: str = Depends(get_admin_user)):
    """Suspende cuenta de usuario."""
    cursor = conn.cursor()
    query = "UPDATE usuarios SET estado = 'suspendido' WHERE id_usuario = %s"
    cursor.execute(query, (id,))
    conn.commit()
    cursor.close()
    return {"status": "suspended"}

@router.patch("/users/{id}/reactivate")
def reactivate_user(id: str, conn = Depends(get_db_connection), admin_id: str = Depends(get_admin_user)):
    """Activa cuenta suspendida."""
    cursor = conn.cursor()
    query = "UPDATE usuarios SET estado = 'activo' WHERE id_usuario = %s"
    cursor.execute(query, (id,))
    conn.commit()
    cursor.close()
    return {"status": "active"}

@router.get("/offers", response_model=List[OfferResponse])
def get_offers(conn = Depends(get_db_connection), admin_id: str = Depends(get_admin_user)):
    """Lista todas las ofertas."""
    cursor = conn.cursor()
    query = """
        SELECT o.*, a.titulo as articulo_titulo
        FROM ofertas o
        LEFT JOIN articulos a ON o.id_articulo = a.id_articulo
        ORDER BY o.created_at DESC
    """
    cursor.execute(query)
    offers = cursor.fetchall()
    cursor.close()
    
    for o in offers:
        if not o["articulo_titulo"]: o["articulo_titulo"] = "Artículo borrado"
    return offers
