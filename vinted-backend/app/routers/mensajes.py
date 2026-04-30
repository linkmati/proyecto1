from fastapi import APIRouter, Depends, HTTPException
from supabase import Client
from app.db.supabase import get_supabase, get_supabase_admin
from app.core.security import get_current_user
from app.models.schemas import MensajeCreate, MensajeResponse, ConversacionResponse

router = APIRouter(prefix="/api/mensajes", tags=["Mensajes"])

@router.post("/", response_model=MensajeResponse)
def enviar_mensaje(
    mensaje: MensajeCreate,
    db: Client = Depends(get_supabase),
    admin_db: Client = Depends(get_supabase_admin),
    user_id: str = Depends(get_current_user)
):
    """
    Sends a message. Creates a conversation if it doesn't exist.
    Uses ADMIN client to bypass RLS.
    """
    try:
        # 1. Get Article Seller to identify participants
        art_res = db.table("articulos").select("id_vendedor").eq("id_articulo", mensaje.id_articulo).execute()
        if not art_res.data:
            raise HTTPException(status_code=404, detail="Article not found")
        
        # Determine id_usuario_1 and id_usuario_2 (sort to maintain unique constraint)
        u1, u2 = sorted([user_id, mensaje.id_destinatario])
        
        # 2. Find or Create Conversation (Admin client)
        conv_res = admin_db.table("conversaciones").select("*") \
            .eq("id_usuario_1", u1) \
            .eq("id_usuario_2", u2) \
            .eq("id_articulo", mensaje.id_articulo) \
            .execute()
            
        if not conv_res.data:
            new_conv = admin_db.table("conversaciones").insert({
                "id_usuario_1": u1,
                "id_usuario_2": u2,
                "id_articulo": mensaje.id_articulo
            }).execute()
            id_conversacion = new_conv.data[0]["id_conversacion"]
        else:
            id_conversacion = conv_res.data[0]["id_conversacion"]

        # 3. Insert Message (Admin client)
        msg_data = {
            "id_conversacion": id_conversacion,
            "id_emisor": user_id,
            "contenido": mensaje.contenido,
            "leido": False
        }
        
        res = admin_db.table("mensajes").insert(msg_data).execute()
        return res.data[0]

    except Exception as e:
        print(f"Message error: {e}")
        raise HTTPException(status_code=500, detail=str(e))

@router.get("/conversaciones", response_model=list[dict])
def listar_conversaciones(
    db: Client = Depends(get_supabase),
    user_id: str = Depends(get_current_user)
):
    """
    Lists conversations where the user is a participant. 
    Includes unread counts and is ordered by the latest message.
    """
    try:
        # 1. Traemos conversaciones con información básica
        response = db.table("conversaciones") \
            .select("*, articulos(titulo), usuario1:usuarios!id_usuario_1(email), usuario2:usuarios!id_usuario_2(email)") \
            .or_(f"id_usuario_1.eq.{user_id},id_usuario_2.eq.{user_id}") \
            .execute()
        
        formatted = []
        for conv in response.data:
            # 2. Por cada conversación, buscamos el último mensaje para ordenar
            last_msg = db.table("mensajes") \
                .select("created_at") \
                .eq("id_conversacion", conv["id_conversacion"]) \
                .order("created_at", desc=True) \
                .limit(1) \
                .execute()
            
            # 3. Contamos mensajes no leídos del OTRO emisor
            unread_res = db.table("mensajes") \
                .select("id_mensaje", count="exact") \
                .eq("id_conversacion", conv["id_conversacion"]) \
                .neq("id_emisor", user_id) \
                .eq("leido", False) \
                .execute()

            # Determinamos quién es el 'otro' usuario
            es_usuario_1 = conv["id_usuario_1"] == user_id
            otro_usuario_email = conv["usuario2"]["email"] if es_usuario_1 else conv["usuario1"]["email"]
            
            # Usamos el timestamp del último mensaje o el de creación del chat si no hay mensajes
            last_activity = last_msg.data[0]["created_at"] if last_msg.data else conv["created_at"]

            formatted.append({
                "id_conversacion": conv["id_conversacion"],
                "id_articulo": conv["id_articulo"],
                "titulo_articulo": conv["articulos"]["titulo"],
                "nombre_otro": otro_usuario_email.split("@")[0],
                "id_usuario_1": conv["id_usuario_1"],
                "id_usuario_2": conv["id_usuario_2"],
                "unread_count": unread_res.count or 0,
                "last_activity": last_activity
            })
        
        # 4. Ordenamos por actividad más reciente (descendente)
        formatted.sort(key=lambda x: x["last_activity"], reverse=True)
            
        return formatted
    except Exception as e:
        print(f"Error listing conversations: {e}")
        raise HTTPException(status_code=500, detail=str(e))

@router.get("/no-leidos/conteo")
def contar_no_leidos(
    db: Client = Depends(get_supabase),
    user_id: str = Depends(get_current_user)
):
    """
    Counts unread messages for the current user.
    """
    try:
        # Buscamos mensajes donde leido=False, el emisor NO sea el usuario actual,
        # y el usuario sea parte de la conversación.
        
        # 1. Obtener IDs de mis conversaciones
        convs = db.table("conversaciones") \
            .select("id_conversacion") \
            .or_(f"id_usuario_1.eq.{user_id},id_usuario_2.eq.{user_id}") \
            .execute()
        
        if not convs.data:
            return {"count": 0}
            
        conv_ids = [c["id_conversacion"] for c in convs.data]
        
        # 2. Contar mensajes no leídos en esas conversaciones (donde yo no soy el emisor)
        msg_res = db.table("mensajes") \
            .select("id_mensaje", count="exact") \
            .in_("id_conversacion", conv_ids) \
            .neq("id_emisor", user_id) \
            .eq("leido", False) \
            .execute()
            
        return {"count": msg_res.count}
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@router.patch("/conversaciones/{id_conversacion}/leer")
def marcar_como_leido(
    id_conversacion: int,
    db: Client = Depends(get_supabase),
    admin_db: Client = Depends(get_supabase_admin),
    user_id: str = Depends(get_current_user)
):
    """
    Marks all messages in a conversation as read (those not sent by current user).
    """
    try:
        # Usamos admin_db para asegurar el update si hay restricciones de RLS
        admin_db.table("mensajes") \
            .update({"leido": True}) \
            .eq("id_conversacion", id_conversacion) \
            .neq("id_emisor", user_id) \
            .execute()
        return {"status": "success"}
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@router.get("/conversaciones/{id_conversacion}", response_model=list[MensajeResponse])
def listar_mensajes_conversacion(
    id_conversacion: int,
    db: Client = Depends(get_supabase),
    user_id: str = Depends(get_current_user)
):
    """
    Lists messages in a conversation.
    """
    try:
        # Verify user is part of the conversation
        conv_res = db.table("conversaciones").select("*").eq("id_conversacion", id_conversacion).execute()
        if not conv_res.data:
            raise HTTPException(status_code=404, detail="Conversation not found")
        
        conv = conv_res.data[0]
        if user_id not in [conv["id_usuario_1"], conv["id_usuario_2"]]:
            raise HTTPException(status_code=403, detail="Unauthorized")

        response = db.table("mensajes").select("*") \
            .eq("id_conversacion", id_conversacion) \
            .order("id_mensaje", desc=False) \
            .execute()
        return response.data
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))
