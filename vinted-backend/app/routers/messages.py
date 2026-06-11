from fastapi import APIRouter, Depends, HTTPException
from typing import List, Dict
from app.db.supabase import get_db_connection
from app.core.security import get_current_user

router = APIRouter(prefix="/api/messages", tags=["Messages"])

@router.get("/conversations", response_model=List[Dict])
def listar_chats(conn = Depends(get_db_connection), user_id: str = Depends(get_current_user)):
    """Saca la lista de chats abiertos de forma sencilla."""
    with conn.cursor() as cur:
        # Pilla las conversaciones básicas
        cur.execute("""
            SELECT * FROM conversaciones 
            WHERE id_usuario_1 = %s OR id_usuario_2 = %s
        """, (user_id, user_id))
        filas = cur.fetchall()
        
        lista_final = []
        for f in filas:
            # 1. Título del artículo
            cur.execute("SELECT titulo FROM articulos WHERE id_articulo = %s", (f["id_articulo"],))
            art = cur.fetchone()
            titulo = art["titulo"] if art else "Borrado"
            
            # 2. Datos del otro usuario
            otro_id = f["id_usuario_2"] if str(f["id_usuario_1"]) == user_id else f["id_usuario_1"]
            cur.execute("SELECT nombre_usuario, email FROM usuarios WHERE id_usuario = %s", (otro_id,))
            usu = cur.fetchone()
            nombre = (usu["nombre_usuario"] or usu["email"].split("@")[0]) if usu else "Desconocido"
            
            # 3. Último mensaje
            cur.execute("""
                SELECT contenido, created_at FROM mensajes 
                WHERE id_conversacion = %s 
                ORDER BY created_at DESC LIMIT 1
            """, (f["id_conversacion"],))
            msj = cur.fetchone()
            
            # 4. Mensajes sin leer
            cur.execute("""
                SELECT COUNT(*) as n FROM mensajes 
                WHERE id_conversacion = %s AND id_emisor != %s AND leido = False
            """, (f["id_conversacion"], user_id))
            cont = cur.fetchone()
            
            lista_final.append({
                "id_conversacion": f["id_conversacion"],
                "item_title": titulo,
                "other_user_name": nombre,
                "last_message": msj["contenido"] if msj else "Sin mensajes",
                "unread_count": cont["n"] if cont else 0,
                "last_activity": msj["created_at"] if msj else f["created_at"]
            })
            
    # Ordenar por fecha a mano
    lista_final.sort(key=lambda x: x["last_activity"], reverse=True)
    return lista_final

@router.get("/conversations/{id}/messages")
async def ver_chat(id: int, conn = Depends(get_db_connection), user_id: str = Depends(get_current_user)):
    """Pilla todos los mensajes de un chat."""
    with conn.cursor() as cur:
        # Ver si el usuario está metido en el chat
        cur.execute("SELECT * FROM conversaciones WHERE id_conversacion = %s", (id,))
        c = cur.fetchone()
        if not c or user_id not in [str(c["id_usuario_1"]), str(c["id_usuario_2"])]:
            raise HTTPException(403, "No puedes ver este chat")
            
        # Mensajes
        cur.execute("SELECT * FROM mensajes WHERE id_conversacion = %s ORDER BY created_at ASC", (id,))
        mensajes = cur.fetchall()
        
        # Oferta si hay
        cur.execute("""
            SELECT * FROM ofertas WHERE id_articulo = %s 
            AND id_comprador IN (%s, %s)
            ORDER BY updated_at DESC LIMIT 1
        """, (c["id_articulo"], c["id_usuario_1"], c["id_usuario_2"]))
        oferta = cur.fetchone()
        
    return {"messages": mensajes, "offer": oferta}

@router.patch("/conversations/{id}/read")
async def leer(id: int, conn = Depends(get_db_connection), user_id: str = Depends(get_current_user)):
    """Marca como leído lo que te han mandado."""
    with conn.cursor() as cur:
        cur.execute("UPDATE mensajes SET leido = True WHERE id_conversacion = %s AND id_emisor != %s", (id, user_id))
        conn.commit()
    return {"status": "ok"}
