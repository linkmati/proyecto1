from fastapi import APIRouter, Depends, HTTPException
from supabase import Client
from app.db.supabase import get_supabase
from app.core.security import get_current_user
from app.models.schemas import MensajeCreate, MensajeResponse, ConversacionResponse

router = APIRouter(prefix="/api/mensajes", tags=["Mensajes"])

@router.post("/", response_model=MensajeResponse)
def enviar_mensaje(
    mensaje: MensajeCreate,
    db: Client = Depends(get_supabase),
    user_id: str = Depends(get_current_user)
):
    """
    Sends a message. Creates a conversation if it doesn't exist.
    """
    try:
        # 1. Get Article Seller to identify participants
        art_res = db.table("articulos").select("id_vendedor").eq("id_articulo", mensaje.id_articulo).execute()
        if not art_res.data:
            raise HTTPException(status_code=404, detail="Article not found")
        
        seller_id = art_res.data[0]["id_vendedor"]
        
        # Determine id_usuario_1 and id_usuario_2 (sort by UUID to maintain unique constraint)
        u1, u2 = sorted([user_id, mensaje.id_destinatario])
        
        # 2. Find or Create Conversation
        conv_res = db.table("conversaciones").select("*") \
            .eq("id_usuario_1", u1) \
            .eq("id_usuario_2", u2) \
            .eq("id_articulo", mensaje.id_articulo) \
            .execute()
            
        if not conv_res.data:
            new_conv = db.table("conversaciones").insert({
                "id_usuario_1": u1,
                "id_usuario_2": u2,
                "id_articulo": mensaje.id_articulo
            }).execute()
            id_conversacion = new_conv.data[0]["id_conversacion"]
        else:
            id_conversacion = conv_res.data[0]["id_conversacion"]

        # 3. Insert Message
        msg_data = {
            "id_conversacion": id_conversacion,
            "id_emisor": user_id,
            "contenido": mensaje.contenido,
            "leido": False
        }
        
        res = db.table("mensajes").insert(msg_data).execute()
        return res.data[0]

    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@router.get("/conversaciones", response_model=list[ConversacionResponse])
def listar_conversaciones(
    db: Client = Depends(get_supabase),
    user_id: str = Depends(get_current_user)
):
    """
    Lists conversations the user is part of.
    """
    try:
        response = db.table("conversaciones") \
            .select("*") \
            .or_(f"id_usuario_1.eq.{user_id},id_usuario_2.eq.{user_id}") \
            .execute()
        return response.data
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
