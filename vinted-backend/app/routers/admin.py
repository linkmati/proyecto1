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
        query += " WHERE a.titulo ILIKE %s"
        params.append(f"%{search}%")
    query += " ORDER BY a.created_at DESC"
    
    with conn.cursor() as cur:
        cur.execute(query, tuple(params))
        items = cur.fetchall()
        for i in items:
            cur.execute("SELECT * FROM fotos_articulo WHERE id_articulo = %s", (i["id_articulo"],))
            i["fotos"] = cur.fetchall()
            i["vendedor_nombre"] = i["nombre_usuario"] or i["email"].split("@")[0]
    return items

@router.delete("/items/{id}")
def delete_item(id: int, conn = Depends(get_db_connection), admin_id: str = Depends(get_admin_user)):
    """Eliminación forzosa por admin."""
    with conn.cursor() as cur:
        cur.execute("DELETE FROM articulos WHERE id_articulo = %s", (id,))
        conn.commit()
    return {"status": "deleted"}

@router.get("/users", response_model=List[UserResponse])
def get_users(conn = Depends(get_db_connection), admin_id: str = Depends(get_admin_user)):
    """Lista todos los usuarios."""
    with conn.cursor() as cur:
        cur.execute("SELECT * FROM usuarios ORDER BY created_at DESC")
        return cur.fetchall()

@router.patch("/users/{id}/suspend")
def suspend_user(id: str, conn = Depends(get_db_connection), admin_id: str = Depends(get_admin_user)):
    """Suspende cuenta de usuario."""
    with conn.cursor() as cur:
        cur.execute("UPDATE usuarios SET estado = 'suspendido' WHERE id_usuario = %s", (id,))
        conn.commit()
    return {"status": "suspended"}

@router.patch("/users/{id}/reactivate")
def reactivate_user(id: str, conn = Depends(get_db_connection), admin_id: str = Depends(get_admin_user)):
    """Activa cuenta suspendida."""
    with conn.cursor() as cur:
        cur.execute("UPDATE usuarios SET estado = 'activo' WHERE id_usuario = %s", (id,))
        conn.commit()
    return {"status": "active"}

@router.get("/offers", response_model=List[OfferResponse])
def get_offers(conn = Depends(get_db_connection), admin_id: str = Depends(get_admin_user)):
    """Lista todas las ofertas."""
    with conn.cursor() as cur:
        cur.execute("""
            SELECT o.*, a.titulo as articulo_titulo
            FROM ofertas o
            LEFT JOIN articulos a ON o.id_articulo = a.id_articulo
            ORDER BY o.created_at DESC
        """)
        offers = cur.fetchall()
        for o in offers:
            if not o["articulo_titulo"]: o["articulo_titulo"] = "Artículo borrado"
    return offers
