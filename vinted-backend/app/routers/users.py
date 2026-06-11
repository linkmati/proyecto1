from fastapi import APIRouter, Depends, HTTPException
from typing import List
from app.db.supabase import get_db_connection
from app.core.security import get_current_user
from app.models.schemas import UserResponse, ItemResponse, OrderResponse

router = APIRouter(prefix="/api/users", tags=["Users"])

@router.get("/me", response_model=UserResponse)
def mi_perfil(conn = Depends(get_db_connection), user_id: str = Depends(get_current_user)):
    """Pilla mis datos de usuario de la tabla 'usuarios'."""
    with conn.cursor() as cur:
        cur.execute("SELECT * FROM usuarios WHERE id_usuario = %s", (user_id,))
        usuario = cur.fetchone()
    if not usuario: 
        raise HTTPException(status_code=404, detail="No te he encontrado en la base de datos")
    return usuario

@router.get("/me/items", response_model=List[ItemResponse])
def mis_productos(conn = Depends(get_db_connection), user_id: str = Depends(get_current_user)):
    """Lista todos los artículos que yo he subido."""
    with conn.cursor() as cur:
        cur.execute("SELECT * FROM articulos WHERE id_vendedor = %s", (user_id,))
        trastos = cur.fetchall()
        # Para cada uno buscamos sus fotos
        for t in trastos:
            cur.execute("SELECT * FROM fotos_articulo WHERE id_articulo = %s", (t["id_articulo"],))
            t["fotos"] = cur.fetchall()
    return trastos

@router.get("/me/favorites", response_model=List[ItemResponse])
def mis_favoritos(conn = Depends(get_db_connection), user_id: str = Depends(get_current_user)):
    """Artículos que he marcado con el corazón."""
    with conn.cursor() as cur:
        cur.execute("""
            SELECT a.* FROM articulos a
            JOIN favoritos f ON a.id_articulo = f.id_articulo
            WHERE f.id_usuario = %s
        """, (user_id,))
        cosas = cur.fetchall()
        for c in cosas:
            cur.execute("SELECT * FROM fotos_articulo WHERE id_articulo = %s", (c["id_articulo"],))
            c["fotos"] = cur.fetchall()
    return cosas

@router.get("/me/purchases", response_model=List[OrderResponse])
def mis_compras(conn = Depends(get_db_connection), user_id: str = Depends(get_current_user)):
    """Todo lo que he comprado o tengo apalabrado."""
    with conn.cursor() as cur:
        # 1. Compras que ya están en la tabla de pedidos
        cur.execute("""
            SELECT id_pedido, id_comprador, id_articulo, estado_pedido, precio_final, created_at
            FROM pedidos WHERE id_comprador = %s
        """, (user_id,))
        compras = cur.fetchall()
        
        id_articulos_pedidos = [c["id_articulo"] for c in compras]
        
        # 2. Ofertas aceptadas (que son como una compra pero sin pedido formal todavía)
        cur.execute("""
            SELECT id_oferta as id_pedido, id_comprador, id_articulo, 'completado' as estado_pedido, importe as precio_final, created_at
            FROM ofertas WHERE id_comprador = %s AND estado = 'aceptada'
        """, (user_id,))
        for o in cur.fetchall():
            if o["id_articulo"] not in id_articulos_pedidos: 
                compras.append(o)

        # 3. Rellenamos la info del artículo para que el frontend pueda mostrar la foto y el título
        for c in compras:
            cur.execute("SELECT * FROM articulos WHERE id_articulo = %s", (c["id_articulo"],))
            c["articulo"] = cur.fetchone()
            if c["articulo"]:
                cur.execute("SELECT * FROM fotos_articulo WHERE id_articulo = %s", (c["id_articulo"],))
                c["articulo"]["fotos"] = cur.fetchall()
                
    return compras
