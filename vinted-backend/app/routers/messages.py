from fastapi import APIRouter, Depends, HTTPException
from typing import List, Dict
from app.db.supabase import get_db_connection
from app.core.security import get_current_user

router = APIRouter(prefix="/api/messages", tags=["Messages"])

@router.get("/conversations", response_model=List[Dict])
def listar_chats(conn = Depends(get_db_connection), user_id: str = Depends(get_current_user)):
    """Saca la lista de chats abiertos de forma sencilla."""
    cursor = conn.cursor()
    # Pilla las conversaciones básicas
    query = """
        SELECT * FROM conversaciones 
        WHERE id_usuario_1 = %s OR id_usuario_2 = %s
    """
    cursor.execute(query, (user_id, user_id))
    filas = cursor.fetchall()
    
    lista_final = []
    for f in filas:
        # 1. Título del artículo
        query_art = "SELECT titulo FROM articulos WHERE id_articulo = %s"
        cursor.execute(query_art, (f["id_articulo"],))
        art = cursor.fetchone()
        titulo = art["titulo"] if art else "Borrado"
        
        # 2. Datos del otro usuario
        otro_id = f["id_usuario_2"] if str(f["id_usuario_1"]) == user_id else f["id_usuario_1"]
        query_usu = "SELECT nombre_usuario, email FROM usuarios WHERE id_usuario = %s"
        cursor.execute(query_usu, (otro_id,))
        usu = cursor.fetchone()
        nombre = (usu["nombre_usuario"] or usu["email"].split("@")[0]) if usu else "Desconocido"
        
        # 3. Último mensaje
        query_msj = """
            SELECT contenido, created_at FROM mensajes 
            WHERE id_conversacion = %s 
            ORDER BY created_at DESC LIMIT 1
        """
        cursor.execute(query_msj, (f["id_conversacion"],))
        msj = cursor.fetchone()
        
        # 4. Mensajes sin leer
        query_cont = """
            SELECT COUNT(*) as n FROM mensajes 
            WHERE id_conversacion = %s AND id_emisor != %s AND leido = False
        """
        cursor.execute(query_cont, (f["id_conversacion"], user_id))
        cont = cursor.fetchone()
        
        lista_final.append({
            "id_conversacion": f["id_conversacion"],
            "item_title": titulo,
            "other_user_name": nombre,
            "last_message": msj["contenido"] if msj else "Sin mensajes",
            "unread_count": cont["n"] if cont else 0,
            "last_activity": msj["created_at"] if msj else f["created_at"]
        })
        
    cursor.close()
    
    # Ordenar por fecha a mano
    lista_final.sort(key=lambda x: x["last_activity"], reverse=True)
    return lista_final

@router.get("/conversations/{id}/messages")
async def ver_chat(id: int, conn = Depends(get_db_connection), user_id: str = Depends(get_current_user)):
    """Pilla todos los mensajes de un chat."""
    cursor = conn.cursor()
    
    # Ver si el usuario está metido en el chat
    query_c = "SELECT * FROM conversaciones WHERE id_conversacion = %s"
    cursor.execute(query_c, (id,))
    c = cursor.fetchone()
    if not c or user_id not in [str(c["id_usuario_1"]), str(c["id_usuario_2"])]:
        cursor.close()
        raise HTTPException(403, "No puedes ver este chat")
        
    # Mensajes
    query_msgs = "SELECT * FROM mensajes WHERE id_conversacion = %s ORDER BY created_at ASC"
    cursor.execute(query_msgs, (id,))
    mensajes = cursor.fetchall()
    
    # Oferta si hay
    query_of = """
        SELECT * FROM ofertas WHERE id_articulo = %s 
        AND id_comprador IN (%s, %s)
        ORDER BY updated_at DESC LIMIT 1
    """
    cursor.execute(query_of, (c["id_articulo"], c["id_usuario_1"], c["id_usuario_2"]))
    oferta = cursor.fetchone()
    
    cursor.close()
    return {"messages": mensajes, "offer": oferta}

@router.patch("/conversations/{id}/read")
async def leer(id: int, conn = Depends(get_db_connection), user_id: str = Depends(get_current_user)):
    """Marca como leído lo que te han mandado."""
    cursor = conn.cursor()
    query = "UPDATE mensajes SET leido = True WHERE id_conversacion = %s AND id_emisor != %s"
    cursor.execute(query, (id, user_id))
    conn.commit()
    cursor.close()
    return {"status": "ok"}

# --- NUEVOS ENDPOINTS PARA MENSAJERÍA ---

from pydantic import BaseModel

class MessageCreate(BaseModel):
    id_destinatario: str
    id_articulo: int
    contenido: str

@router.get("/unread-count")
def contar_no_leidos(conn = Depends(get_db_connection), user_id: str = Depends(get_current_user)):
    """Cuenta el número total de mensajes sin leer del usuario."""
    cursor = conn.cursor()
    query = """
        SELECT COUNT(*) as n FROM mensajes m
        JOIN conversaciones c ON m.id_conversacion = c.id_conversacion
        WHERE (c.id_usuario_1 = %s OR c.id_usuario_2 = %s)
          AND m.id_emisor != %s
          AND m.leido = False
    """
    cursor.execute(query, (user_id, user_id, user_id))
    fila = cursor.fetchone()
    cursor.close()
    return {"count": fila["n"] if fila else 0}

@router.post("")
def enviar_mensaje(datos: MessageCreate, conn = Depends(get_db_connection), user_id: str = Depends(get_current_user)):
    """Envía un mensaje e inicia/recupera la conversación."""
    cursor = conn.cursor()
    try:
        # Ordenamos los usuarios para mantener unicidad en id_usuario_1 < id_usuario_2
        u1, u2 = sorted([user_id, datos.id_destinatario])
        
        # Comprobar si existe la conversación
        cursor.execute(
            "SELECT id_conversacion FROM conversaciones WHERE id_usuario_1 = %s AND id_usuario_2 = %s AND id_articulo = %s",
            (u1, u2, datos.id_articulo)
        )
        fila_conv = cursor.fetchone()
        if not fila_conv:
            cursor.execute(
                "INSERT INTO conversaciones (id_usuario_1, id_usuario_2, id_articulo) VALUES (%s, %s, %s)",
                (u1, u2, datos.id_articulo)
            )
            cursor.execute("SELECT lastval()")
            cid = cursor.fetchone()["lastval"]
        else:
            cid = fila_conv["id_conversacion"]
            
        # Insertar mensaje
        cursor.execute(
            "INSERT INTO mensajes (id_conversacion, id_emisor, contenido) VALUES (%s, %s, %s)",
            (cid, user_id, datos.contenido)
        )
        
        # Obtener el mensaje creado para responder
        cursor.execute("SELECT lastval()")
        mid = cursor.fetchone()["lastval"]
        cursor.execute("SELECT * FROM mensajes WHERE id_mensaje = %s", (mid,))
        nuevo_msj = cursor.fetchone()
        
        conn.commit()
        cursor.close()
        return nuevo_msj
    except Exception as e:
        conn.rollback()
        cursor.close()
        raise HTTPException(500, "Error al enviar el mensaje")

