from fastapi import APIRouter, Depends, HTTPException
from typing import List, Dict
from app.db.supabase import get_db_connection
from app.core.security import get_current_user
from app.models.schemas import OfferCreate, OfferResponse

router = APIRouter(prefix="/api/offers", tags=["Offers"])

# --- COSAS PARA NO REPETIR ---

async def pillar_oferta(id: int, conn):
    """Busca una oferta por su ID."""
    with conn.cursor() as cur:
        cur.execute("SELECT * FROM ofertas WHERE id_oferta = %s", (id,))
        o = cur.fetchone()
    if not o: raise HTTPException(404, "Oferta no encontrada")
    return o

async def ver_si_es_mi_oferta(id: int, user_id: str, conn):
    """Comprueba si el usuario es el comprador o el vendedor del artículo."""
    o = await pillar_oferta(id, conn)
    # Buscamos el artículo para saber quién es el vendedor
    with conn.cursor() as cur:
        cur.execute("SELECT id_vendedor FROM articulos WHERE id_articulo = %s", (o["id_articulo"],))
        art = cur.fetchone()
    
    if str(o["id_comprador"]) != user_id and str(art["id_vendedor"]) != user_id:
        raise HTTPException(403, "No tienes permiso para ver esta oferta")
    return {**o, "vendedor_id": art["id_vendedor"]}

# --- RUTAS ---

@router.get("", response_model=List[Dict])
def mis_ofertas(conn = Depends(get_db_connection), user_id: str = Depends(get_current_user)):
    """Lista las ofertas que he mandado o me han mandado."""
    with conn.cursor() as cur:
        # Consulta plana para no liarnos
        cur.execute("""
            SELECT o.*, u.email as comprador_email, a.titulo as item_title, a.id_vendedor
            FROM ofertas o
            LEFT JOIN usuarios u ON o.id_comprador = u.id_usuario
            LEFT JOIN articulos a ON o.id_articulo = a.id_articulo
            WHERE o.id_comprador = %s OR a.id_vendedor = %s
            ORDER BY o.updated_at DESC
        """, (user_id, user_id))
        filas = cur.fetchall()
        
        for o in filas:
            o["buyer_name"] = (o.pop("comprador_email") or "Usuario").split("@")[0]
            
    return filas

@router.post("", response_model=OfferResponse)
async def crear_oferta(datos: OfferCreate, conn = Depends(get_db_connection), user_id: str = Depends(get_current_user)):
    """Manda una oferta por un producto."""
    try:
        with conn.cursor() as cur:
            # 1. ¿Está disponible?
            cur.execute("SELECT id_vendedor, estado_articulo FROM articulos WHERE id_articulo = %s", (datos.id_articulo,))
            art = cur.fetchone()
            if not art or art["estado_articulo"] != "disponible":
                raise HTTPException(400, "Producto no disponible")
            if str(art["id_vendedor"]) == user_id:
                raise HTTPException(400, "Es tu propio producto...")

            # 2. Guardar oferta
            cur.execute("""
                INSERT INTO ofertas (importe, id_articulo, id_comprador, ultimo_emisor_id, estado, mensaje)
                VALUES (%s, %s, %s, %s, 'pendiente', %s) RETURNING *
            """, (datos.importe, datos.id_articulo, user_id, user_id, datos.mensaje))
            nueva = cur.fetchone()
            
            # 3. Chat (muy manual)
            u1, u2 = sorted([user_id, str(art["id_vendedor"])])
            cur.execute("""
                INSERT INTO conversaciones (id_usuario_1, id_usuario_2, id_articulo)
                VALUES (%s, %s, %s) ON CONFLICT DO NOTHING
            """, (u1, u2, datos.id_articulo))
            
            cur.execute("SELECT id_conversacion FROM conversaciones WHERE id_usuario_1=%s AND id_usuario_2=%s AND id_articulo=%s", (u1, u2, datos.id_articulo))
            cid = cur.fetchone()["id_conversacion"]
            
            msg = f"Oferta de €{datos.importe}."
            cur.execute("INSERT INTO mensajes (id_conversacion, id_emisor, contenido) VALUES (%s, %s, %s)", (cid, user_id, msg))
            
            conn.commit()
            return nueva
    except Exception as e:
        conn.rollback()
        raise e if isinstance(e, HTTPException) else HTTPException(500, "Fallo al ofertar")

@router.post("/{id}/accept")
async def aceptar(id: int, conn = Depends(get_db_connection), user_id: str = Depends(get_current_user)):
    """Si se acepta, el trasto se vende."""
    o = await ver_si_es_mi_oferta(id, user_id, conn)
    if str(o["ultimo_emisor_id"]) == user_id:
        raise HTTPException(400, "Tienes que esperar a que el otro acepte")

    try:
        with conn.cursor() as cur:
            # Producto vendido
            cur.execute("UPDATE articulos SET estado_articulo = 'vendido' WHERE id_articulo = %s", (o["id_articulo"],))
            # Oferta aceptada
            cur.execute("UPDATE ofertas SET estado = 'aceptada' WHERE id_oferta = %s", (id,))
            conn.commit()
        return {"message": "¡Vendido!"}
    except Exception:
        conn.rollback()
        raise HTTPException(500, "Fallo al confirmar")
