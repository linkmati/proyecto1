from fastapi import APIRouter, Depends, HTTPException
from supabase import Client
from typing import List, Dict
from app.db.supabase import get_supabase, get_supabase_admin
from app.core.security import get_current_user
from app.models.schemas import MessageCreate, MessageResponse

router = APIRouter(prefix="/api/messages", tags=["Messages"])

# --- Internal Helpers (Dependencies) ---

async def get_conversation_or_404(conversation_id: int, db: Client = Depends(get_supabase_admin)):
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
    db: Client = Depends(get_supabase_admin)
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
    db: Client = Depends(get_supabase_admin),
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
        # We use db (admin) to handle conversation creation safely
        conv_res = db.table("conversaciones").select("id_conversacion") \
            .eq("id_usuario_1", u1) \
            .eq("id_usuario_2", u2) \
            .eq("id_articulo", message_data.id_articulo) \
            .execute()
            
        if not conv_res.data:
            new_conv = db.table("conversaciones").insert({
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
        
        result = db.table("mensajes").insert(new_message).execute()
        return result.data[0]

    except Exception as e:
        if isinstance(e, HTTPException): raise e
        raise HTTPException(status_code=500, detail=str(e))

@router.get("/conversations", response_model=List[Dict])
def list_conversations(
    db: Client = Depends(get_supabase_admin),
    user_id: str = Depends(get_current_user)
):
    """
    Lists all conversations for the current user with unread counts and latest activity.
    """
    print(f"DEBUG - list_conversations START for user {user_id}")
    try:
        # Step 1: Fetch conversations where user is participant 1 or 2
        response = db.table("conversaciones") \
            .select("*, articulos(titulo), usuario1:usuarios!id_usuario_1(nombre_usuario, email), usuario2:usuarios!id_usuario_2(nombre_usuario, email)") \
            .or_(f"id_usuario_1.eq.{user_id},id_usuario_2.eq.{user_id}") \
            .execute()
        
        print(f"DEBUG - list_conversations: Found {len(response.data)} raw conversations")
        
        formatted_list = []
        for conv in response.data:
            try:
                conv_id = conv["id_conversacion"]
                
                # Fetch last message and unread count
                last_msg_res = db.table("mensajes") \
                    .select("contenido, created_at") \
                    .eq("id_conversacion", conv_id) \
                    .order("created_at", desc=True) \
                    .limit(1) \
                    .execute()
                
                unread_res = db.table("mensajes") \
                    .select("id_mensaje", count="exact") \
                    .eq("id_conversacion", conv_id) \
                    .neq("id_emisor", user_id) \
                    .eq("leido", False) \
                    .execute()

                # Identify the other person safely
                is_user_1 = str(conv["id_usuario_1"]) == str(user_id)
                
                def get_user_info(user_data):
                    if not user_data: return {"nombre_usuario": "Usuario", "email": ""}
                    if isinstance(user_data, list): user_data = user_data[0]
                    return {
                        "nombre": user_data.get("nombre_usuario") or user_data.get("email", "").split("@")[0] or "Usuario",
                        "email": user_data.get("email", "")
                    }
                
                u1_info = get_user_info(conv.get("usuario1"))
                u2_info = get_user_info(conv.get("usuario2"))
                
                art_data = conv.get("articulos")
                if isinstance(art_data, list): art_data = art_data[0] if art_data else {}
                item_title = (art_data or {}).get("titulo", "Artículo no disponible")
                
                other_user = u2_info if is_user_1 else u1_info
                activity_time = last_msg_res.data[0]["created_at"] if last_msg_res.data else conv["created_at"]
                last_text = last_msg_res.data[0]["contenido"] if last_msg_res.data else "Sin mensajes"

                item_to_add = {
                    "id_conversacion": conv_id,
                    "id_articulo": conv["id_articulo"],
                    "id_usuario_1": conv["id_usuario_1"],
                    "id_usuario_2": conv["id_usuario_2"],
                    "item_title": item_title,
                    "other_user_name": other_user["nombre"],
                    "last_message": last_text,
                    "unread_count": unread_res.count or 0,
                    "last_activity": activity_time
                }
                print(f"DEBUG - list_conversations: Adding conversation {conv_id} with {item_to_add['other_user_name']}")
                formatted_list.append(item_to_add)
            except Exception as loop_err:
                print(f"DEBUG - Error in conversation loop for {conv.get('id_conversacion')}: {loop_err}")
                continue
        
        formatted_list.sort(key=lambda x: x["last_activity"], reverse=True)
        return formatted_list

    except Exception as e:
        print(f"DEBUG - list_conversations top-level error: {str(e)}")
        raise HTTPException(status_code=500, detail=str(e))

@router.get("/conversations/{conversation_id}/messages", response_model=Dict)
async def list_conversation_messages(
    conversation_id: int,
    db: Client = Depends(get_supabase_admin),
    conversation: dict = Depends(verify_conversation_participant)
):
    """
    Returns all messages for a specific conversation and any active offer linked to the item.
    """
    try:
        # Fetch Messages
        msg_res = db.table("mensajes").select("*") \
            .eq("id_conversacion", conversation_id) \
            .order("id_mensaje", desc=False) \
            .execute()
        
        # Fetch related offer (active offer for this item and these users)
        offer_res = db.table("ofertas") \
            .select("*") \
            .eq("id_articulo", conversation["id_articulo"]) \
            .in_("id_comprador", [conversation["id_usuario_1"], conversation["id_usuario_2"]]) \
            .order("updated_at", desc=True) \
            .limit(1) \
            .execute()
            
        return {
            "messages": msg_res.data,
            "offer": offer_res.data[0] if offer_res.data else None
        }
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
    db: Client = Depends(get_supabase_admin),
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
