from fastapi import APIRouter, Depends, HTTPException
from supabase import Client
from typing import List, Dict
from app.db.supabase import get_supabase, get_supabase_admin
from app.core.security import get_current_user
from app.models.schemas import MessageCreate, MessageResponse

router = APIRouter(prefix="/api/messages", tags=["Messages"])

# --- Internal Helpers (Dependencies) ---

async def get_conversation_or_404(conversation_id: int, db: Client = Depends(get_supabase)):
    """
    Helper to fetch a conversation and ensure it exists.
    """
    response = db.table("conversaciones").select("*").eq("id_conversacion", conversation_id).execute()
    if not response.data:
        raise HTTPException(status_code=404, detail="Conversation not found")
    return response.data[0]

async def verify_conversation_participant(
    conversation_id: int, 
    user_id: str = Depends(get_current_user),
    db: Client = Depends(get_supabase)
):
    """
    Security check: Ensures the user is part of the conversation.
    """
    conversation = await get_conversation_or_404(conversation_id, db)
    if user_id not in [conversation["id_usuario_1"], conversation["id_usuario_2"]]:
        raise HTTPException(status_code=403, detail="You are not a participant in this conversation")
    return conversation

# --- API Routes ---

@router.post("", response_model=MessageResponse)
async def send_message(
    message_data: MessageCreate,
    db: Client = Depends(get_supabase),
    admin_db: Client = Depends(get_supabase_admin),
    user_id: str = Depends(get_current_user)
):
    """
    Sends a message. Creates a conversation if it doesn't already exist.
    """
    try:
        # 1. Verify item exists and get seller ID
        item_res = db.table("articulos").select("id_vendedor").eq("id_articulo", message_data.id_articulo).execute()
        if not item_res.data:
            raise HTTPException(status_code=404, detail="Item not found")
        
        # 2. Setup participants (sorted to ensure unique conversation per item/users)
        u1, u2 = sorted([user_id, message_data.id_destinatario])
        
        # 3. Find or Create Conversation
        # We use admin_db to handle conversation creation safely
        conv_res = admin_db.table("conversaciones").select("id_conversacion") \
            .eq("id_usuario_1", u1) \
            .eq("id_usuario_2", u2) \
            .eq("id_articulo", message_data.id_articulo) \
            .execute()
            
        if not conv_res.data:
            new_conv = admin_db.table("conversaciones").insert({
                "id_usuario_1": u1,
                "id_usuario_2": u2,
                "id_articulo": message_data.id_articulo
            }).execute()
            conversation_id = new_conv.data[0]["id_conversacion"]
        else:
            conversation_id = conv_res.data[0]["id_conversacion"]

        # 4. Save the Message
        new_message = {
            "id_conversacion": conversation_id,
            "id_emisor": user_id,
            "contenido": message_data.contenido,
            "leido": False
        }
        
        result = admin_db.table("mensajes").insert(new_message).execute()
        return result.data[0]

    except Exception as e:
        if isinstance(e, HTTPException): raise e
        raise HTTPException(status_code=500, detail=str(e))

@router.get("/conversations", response_model=List[Dict])
def list_conversations(
    db: Client = Depends(get_supabase),
    user_id: str = Depends(get_current_user)
):
    """
    Lists all conversations for the current user with unread counts and latest activity.
    """
    try:
        # Step 1: Fetch conversations where user is participant 1 or 2
        response = db.table("conversaciones") \
            .select("*, articulos(titulo), usuario1:usuarios!id_usuario_1(email), usuario2:usuarios!id_usuario_2(email)") \
            .or_(f"id_usuario_1.eq.{user_id},id_usuario_2.eq.{user_id}") \
            .execute()
        
        formatted_list = []
        for conv in response.data:
            # Step 2: Get the timestamp of the very last message in this chat
            last_msg = db.table("mensajes") \
                .select("created_at") \
                .eq("id_conversacion", conv["id_conversacion"]) \
                .order("created_at", desc=True) \
                .limit(1) \
                .execute()
            
            # Step 3: Count messages the user hasn't read yet
            unread_res = db.table("mensajes") \
                .select("id_mensaje", count="exact") \
                .eq("id_conversacion", conv["id_conversacion"]) \
                .neq("id_emisor", user_id) \
                .eq("leido", False) \
                .execute()

            # Identify the other person in the chat
            is_user_1 = conv["id_usuario_1"] == user_id
            other_user_email = conv["usuario2"]["email"] if is_user_1 else conv["usuario1"]["email"]
            
            activity_time = last_msg.data[0]["created_at"] if last_msg.data else conv["created_at"]

            formatted_list.append({
                "id_conversacion": conv["id_conversacion"],
                "id_articulo": conv["id_articulo"],
                "id_usuario_1": conv["id_usuario_1"],
                "id_usuario_2": conv["id_usuario_2"],
                "item_title": conv["articulos"]["titulo"],
                "other_user_name": other_user_email.split("@")[0],
                "unread_count": unread_res.count or 0,
                "last_activity": activity_time
            })
        
        # Step 4: Sort by most recent activity first
        formatted_list.sort(key=lambda x: x["last_activity"], reverse=True)
        return formatted_list

    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@router.get("/conversations/{conversation_id}/messages", response_model=List[MessageResponse])
async def list_conversation_messages(
    conversation_id: int,
    db: Client = Depends(get_supabase),
    # Participant check
    conversation: dict = Depends(verify_conversation_participant)
):
    """
    Returns all messages for a specific conversation.
    """
    try:
        response = db.table("mensajes").select("*") \
            .eq("id_conversacion", conversation_id) \
            .order("id_mensaje", desc=False) \
            .execute()
        return response.data
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@router.patch("/conversations/{conversation_id}/read")
async def mark_conversation_as_read(
    conversation_id: int,
    admin_db: Client = Depends(get_supabase_admin),
    user_id: str = Depends(get_current_user),
    # Participant check
    conversation: dict = Depends(verify_conversation_participant)
):
    """
    Marks all messages in a conversation as read (except those sent by the current user).
    """
    try:
        admin_db.table("mensajes") \
            .update({"leido": True}) \
            .eq("id_conversacion", conversation_id) \
            .neq("id_emisor", user_id) \
            .execute()
        return {"status": "success", "message": "Conversation marked as read"}
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@router.get("/unread-count")
def get_total_unread_count(
    db: Client = Depends(get_supabase),
    user_id: str = Depends(get_current_user)
):
    """
    Returns the total number of unread messages across all conversations.
    """
    try:
        # 1. Get IDs of all conversations the user is in
        convs = db.table("conversaciones") \
            .select("id_conversacion") \
            .or_(f"id_usuario_1.eq.{user_id},id_usuario_2.eq.{user_id}") \
            .execute()
        
        if not convs.data:
            return {"count": 0}
            
        conversation_ids = [c["id_conversacion"] for c in convs.data]
        
        # 2. Count unread messages in those conversations where sender is NOT the current user
        msg_res = db.table("mensajes") \
            .select("id_mensaje", count="exact") \
            .in_("id_conversacion", conversation_ids) \
            .neq("id_emisor", user_id) \
            .eq("leido", False) \
            .execute()
            
        return {"count": msg_res.count or 0}
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))
