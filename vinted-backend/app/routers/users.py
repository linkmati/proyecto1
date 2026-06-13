from fastapi import APIRouter, Depends, HTTPException
from typing import List
from app.db.supabase import get_db_connection
from app.core.security import get_current_user
from app.models.schemas import UserResponse, ItemResponse, OrderResponse

router = APIRouter(prefix="/api/users", tags=["Users"])

@router.get("/me", response_model=UserResponse)
def mi_perfil(conn = Depends(get_db_connection), user_id: str = Depends(get_current_user)):
    """Pilla mis datos de usuario de la tabla 'usuarios'."""
    cursor = conn.cursor()
    query = "SELECT * FROM usuarios WHERE id_usuario = %s"
    cursor.execute(query, (user_id,))
    usuario = cursor.fetchone()
    cursor.close()
    
    if not usuario: 
        raise HTTPException(status_code=404, detail="No te he encontrado en la base de datos")
    return usuario

@router.get("/me/items", response_model=List[ItemResponse])
def mis_productos(conn = Depends(get_db_connection), user_id: str = Depends(get_current_user)):
    """Lista todos los artículos que yo he subido."""
    cursor = conn.cursor()
    query = "SELECT * FROM articulos WHERE id_vendedor = %s"
    cursor.execute(query, (user_id,))
    trastos = cursor.fetchall()
    
    for t in trastos:
        query_fotos = "SELECT * FROM fotos_articulo WHERE id_articulo = %s"
        cursor.execute(query_fotos, (t["id_articulo"],))
        t["fotos"] = cursor.fetchall()
        
    cursor.close()
    return trastos

@router.get("/me/favorites", response_model=List[ItemResponse])
def mis_favoritos(conn = Depends(get_db_connection), user_id: str = Depends(get_current_user)):
    """Artículos que he marcado con el corazón."""
    cursor = conn.cursor()
    query = """
        SELECT a.* FROM articulos a
        JOIN favoritos f ON a.id_articulo = f.id_articulo
        WHERE f.id_usuario = %s
    """
    cursor.execute(query, (user_id,))
    cosas = cursor.fetchall()
    
    for c in cosas:
        query_fotos = "SELECT * FROM fotos_articulo WHERE id_articulo = %s"
        cursor.execute(query_fotos, (c["id_articulo"],))
        c["fotos"] = cursor.fetchall()
        
    cursor.close()
    return cosas

@router.get("/me/purchases", response_model=List[OrderResponse])
def mis_compras(conn = Depends(get_db_connection), user_id: str = Depends(get_current_user)):
    """Todo lo que he comprado o tengo apalabrado."""
    cursor = conn.cursor()
    
    # 1. Compras que ya están en la tabla de pedidos
    query_pedidos = """
        SELECT id_pedido, id_comprador, id_articulo, estado_pedido, precio_final, created_at
        FROM pedidos WHERE id_comprador = %s
    """
    cursor.execute(query_pedidos, (user_id,))
    compras = cursor.fetchall()
    
    id_articulos_pedidos = [c["id_articulo"] for c in compras]
    
    # 2. Ofertas aceptadas
    query_ofertas = """
        SELECT id_oferta as id_pedido, id_comprador, id_articulo, 'completado' as estado_pedido, importe as precio_final, created_at
        FROM ofertas WHERE id_comprador = %s AND estado = 'aceptada'
    """
    cursor.execute(query_ofertas, (user_id,))
    for o in cursor.fetchall():
        if o["id_articulo"] not in id_articulos_pedidos: 
            compras.append(o)

    # 3. Rellenamos la info
    for c in compras:
        query_art = "SELECT * FROM articulos WHERE id_articulo = %s"
        cursor.execute(query_art, (c["id_articulo"],))
        c["articulo"] = cursor.fetchone()
        
        if c["articulo"]:
            query_fotos = "SELECT * FROM fotos_articulo WHERE id_articulo = %s"
            cursor.execute(query_fotos, (c["id_articulo"],))
            c["articulo"]["fotos"] = cursor.fetchall()
            
    cursor.close()
    return compras
