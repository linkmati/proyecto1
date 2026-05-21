from fastapi import APIRouter, Depends, HTTPException
from supabase import Client
from typing import List, Dict
from app.db.supabase import get_supabase, get_supabase_admin
from app.core.security import get_current_user
from app.models.schemas import OfferCreate, OfferResponse, CounterOfferRequest

router = APIRouter(prefix="/api/offers", tags=["Offers"])

# --- Internal Helpers (Dependencies) ---

async def get_offer_or_404(offer_id: int, db: Client = Depends(get_supabase_admin)):
    """
    Helper to fetch an offer and its related item/seller info.
    """
    response = db.table("ofertas") \
        .select("*, items:articulos(id_vendedor, estado_articulo, titulo)") \
        .eq("id_oferta", offer_id) \
        .execute()
    
    if not response.data:
        raise HTTPException(status_code=404, detail="Offer not found")
    return response.data[0]

async def verify_offer_participation(
    offer_id: int, 
    user_id: str = Depends(get_current_user),
    db: Client = Depends(get_supabase_admin)
):
    """
    Security check: Ensures the user is either the buyer or the seller in this offer.
    """
    offer = await get_offer_or_404(offer_id, db)
    is_buyer = offer["id_comprador"] == user_id
    is_seller = offer["items"]["id_vendedor"] == user_id
    
    if not (is_buyer or is_seller):
        raise HTTPException(status_code=403, detail="You are not part of this offer")
    return offer

# --- API Routes ---

@router.get("", response_model=List[Dict])
def list_my_offers(
    db: Client = Depends(get_supabase_admin),
    user_id: str = Depends(get_current_user)
):
    """
    Returns all offers where the user is either the buyer or the seller.
    """
    print(f"DEBUG - list_my_offers START for user {user_id}")
    try:
        # We fetch separately to avoid complex cross-table .or_() filters that can fail in PostgREST
        
        # 1. Offers where user is the BUYER
        res_buyer = db.table("ofertas") \
            .select("*, usuarios!id_comprador(email), articulos(titulo, id_vendedor)") \
            .eq("id_comprador", user_id) \
            .execute()
            
        # 2. Offers where user is the SELLER (via articulos join)
        res_seller = db.table("ofertas") \
            .select("*, usuarios!id_comprador(email), articulos!inner(titulo, id_vendedor)") \
            .eq("articulos.id_vendedor", user_id) \
            .execute()
        
        # Combine and deduplicate
        combined_data = res_buyer.data + res_seller.data
        print(f"DEBUG - list_my_offers: Found {len(combined_data)} raw offers")
        
        # Simple deduplication by id_oferta
        seen_ids = set()
        unique_offers = []
        
        for offer in combined_data:
            try:
                if offer["id_oferta"] not in seen_ids:
                    # Add simplified names for the frontend
                    usuarios = offer.get("usuarios")
                    if isinstance(usuarios, list): usuarios = usuarios[0] if usuarios else {}
                    email = (usuarios or {}).get("email") or "desconocido@vinted.com"
                    offer["buyer_name"] = email.split("@")[0]
                    
                    art = offer.get("articulos")
                    if isinstance(art, list): art = art[0] if art else {}
                    offer["item_title"] = (art or {}).get("titulo", "Artículo eliminado")
                    
                    unique_offers.append(offer)
                    seen_ids.add(offer["id_oferta"])
            except Exception as loop_err:
                print(f"DEBUG - Error in offer loop for {offer.get('id_oferta')}: {loop_err}")
                continue
                
        print(f"DEBUG - list_my_offers: Returning {len(unique_offers)} unique offers")
        return unique_offers
        
    except Exception as e:
        print(f"DEBUG - list_my_offers error: {str(e)}")
        raise HTTPException(status_code=500, detail=f"Error listing offers: {str(e)}")

@router.post("", response_model=OfferResponse)
async def create_offer(
    offer_data: OfferCreate, 
    db: Client = Depends(get_supabase_admin),
    user_id: str = Depends(get_current_user)
):
    """
    Creates a new offer for an item. 
    Also automatically sends a notification message in the chat.
    """
    try:
        # 1. Validation: Item must exist and be available
        item_res = db.table("articulos").select("estado_articulo, id_vendedor, titulo").eq("id_articulo", offer_data.id_articulo).execute()
        if not item_res.data:
            raise HTTPException(status_code=404, detail="Item not found")
            
        item = item_res.data[0]
        if item["estado_articulo"] != "disponible":
            raise HTTPException(status_code=400, detail="This item is no longer available")
             
        if item["id_vendedor"] == user_id:
            raise HTTPException(status_code=400, detail="You cannot make an offer on your own item.")

        # 2. Create the Offer record
        new_offer = {
            "importe": offer_data.importe,
            "id_articulo": offer_data.id_articulo,
            "id_comprador": user_id,
            "ultimo_emisor_id": user_id,
            "estado": "pendiente",
            "mensaje": offer_data.mensaje 
        }
        
        response = db.table("ofertas").insert(new_offer).execute()
        
        # 3. Automatic Chat Message Notification
        try:
            # Find or create a conversation for this offer
            u1, u2 = sorted([user_id, item["id_vendedor"]])
            conv_res = db.table("conversaciones").select("id_conversacion") \
                .eq("id_usuario_1", u1).eq("id_usuario_2", u2).eq("id_articulo", offer_data.id_articulo).execute()
            
            if not conv_res.data:
                new_conv = db.table("conversaciones").insert({"id_usuario_1": u1, "id_usuario_2": u2, "id_articulo": offer_data.id_articulo}).execute()
                conv_id = new_conv.data[0]["id_conversacion"]
            else:
                conv_id = conv_res.data[0]["id_conversacion"]
            
            notification_text = f"He hecho una oferta de €{offer_data.importe}."
            if offer_data.mensaje:
                notification_text += f"\n{offer_data.mensaje}"
                
            db.table("mensajes").insert({
                "id_conversacion": conv_id,
                "id_emisor": user_id,
                "contenido": notification_text,
                "leido": False
            }).execute()
        except Exception as chat_err:
            print(f"DEBUG: Could not send auto-message: {chat_err}")
            
        return response.data[0]
        
    except Exception as e:
        if isinstance(e, HTTPException): raise e
        raise HTTPException(status_code=500, detail=str(e))

@router.post("/{offer_id}/accept", response_model=OfferResponse)
async def accept_offer(
    offer_id: int,
    admin_db: Client = Depends(get_supabase_admin),
    user_id: str = Depends(get_current_user),
    # Participation check dependency
    offer: dict = Depends(verify_offer_participation)
):
    """
    Accepts an offer. Marks the item as 'sold'.
    """
    try:
        # Validation: Only the receiver of the proposal can accept
        if offer["ultimo_emisor_id"] == user_id:
            raise HTTPException(status_code=400, detail="You cannot accept your own proposal. Wait for the other party.")
            
        if offer["estado"] != "pendiente":
            raise HTTPException(status_code=400, detail="This offer is no longer pending.")

        # 1. Update Article to 'vendido' (Sold)
        admin_db.table("articulos").update({"estado_articulo": "vendido"}).eq("id_articulo", offer["id_articulo"]).execute()
        
        # 2. Update Offer to 'aceptada' (Accepted)
        update_res = admin_db.table("ofertas").update({"estado": "aceptada"}).eq("id_oferta", offer_id).execute()
        
        # 3. Notification Message
        try:
            other_user = offer["id_comprador"] if offer["id_comprador"] != user_id else offer["items"]["id_vendedor"]
            u1, u2 = sorted([user_id, other_user])
            conv_res = admin_db.table("conversaciones").select("id_conversacion") \
                .eq("id_usuario_1", u1).eq("id_usuario_2", u2).eq("id_articulo", offer["id_articulo"]).execute()
            
            if conv_res.data:
                admin_db.table("mensajes").insert({
                    "id_conversacion": conv_res.data[0]["id_conversacion"],
                    "id_emisor": user_id,
                    "contenido": f"✅ ¡He aceptado la oferta! Trato cerrado por €{offer['importe']}.",
                    "leido": False
                }).execute()
        except Exception as msg_err:
            print(f"DEBUG: Accept message failed: {msg_err}")

        return update_res.data[0]
        
    except Exception as e:
        if isinstance(e, HTTPException): raise e
        raise HTTPException(status_code=500, detail=str(e))

@router.post("/{offer_id}/reject", response_model=OfferResponse)
async def reject_offer(
    offer_id: int,
    db: Client = Depends(get_supabase_admin),
    # Participation check
    offer: dict = Depends(verify_offer_participation)
):
    """
    Rejects an offer.
    """
    try:
        update_res = db.table("ofertas").update({"estado": "rechazada"}).eq("id_oferta", offer_id).execute()
        return update_res.data[0]
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@router.patch("/{offer_id}/counter-offer", response_model=OfferResponse)
async def make_counter_offer(
    offer_id: int,
    counter_data: CounterOfferRequest,
    admin_db: Client = Depends(get_supabase_admin),
    user_id: str = Depends(get_current_user),
    # Participation check
    offer: dict = Depends(verify_offer_participation)
):
    """
    Proposes a new price for an existing offer.
    """
    try:
        # 1. Update Offer with new amount
        update_fields = {
            "importe": counter_data.nuevo_importe,
            "ultimo_emisor_id": user_id,
            "estado": "pendiente" # Reset status to pending
        }
        if counter_data.mensaje:
            update_fields["mensaje"] = counter_data.mensaje

        update_res = admin_db.table("ofertas").update(update_fields).eq("id_oferta", offer_id).execute()
        
        # 2. Notification Message
        try:
            text = f"He hecho una contraoferta de €{counter_data.nuevo_importe}."
            if counter_data.mensaje: text += f"\n{counter_data.mensaje}"
            
            other_user = offer["id_comprador"] if offer["id_comprador"] != user_id else offer["items"]["id_vendedor"]
            u1, u2 = sorted([user_id, other_user])
            conv_res = admin_db.table("conversaciones").select("id_conversacion") \
                .eq("id_usuario_1", u1).eq("id_usuario_2", u2).eq("id_articulo", offer["id_articulo"]).execute()
            
            if conv_res.data:
                admin_db.table("mensajes").insert({
                    "id_conversacion": conv_res.data[0]["id_conversacion"],
                    "id_emisor": user_id,
                    "contenido": text,
                    "leido": False
                }).execute()
        except Exception as msg_err:
            print(f"DEBUG: Counter message failed: {msg_err}")

        return update_res.data[0]

    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))
