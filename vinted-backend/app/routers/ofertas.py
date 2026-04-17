from fastapi import APIRouter, Depends, HTTPException
from supabase import Client
from app.db.supabase import get_supabase
from app.core.security import get_current_user
from app.models.schemas import OfertaCreate, OfertaResponse, OfertaContra

router = APIRouter(prefix="/api/ofertas", tags=["Ofertas"])

@router.post("/", response_model=OfertaResponse)
def crear_oferta(
    oferta: OfertaCreate, 
    db: Client = Depends(get_supabase),
    user_id: str = Depends(get_current_user)
):
    """
    Creates a new offer for an available item, with an optional message.
    """
    try:
        articulo_res = db.table("articulos").select("estado_articulo, id_vendedor").eq("id_articulo", oferta.id_articulo).execute()
        
        if not articulo_res.data:
            raise HTTPException(status_code=404, detail="Item not found")
            
        articulo = articulo_res.data[0]
        
        # Cambiamos "DISPONIBLE" por "disponible"
        if articulo["estado_articulo"] != "disponible":
            raise HTTPException(status_code=400, detail="This item is no longer available")
             
        if articulo["id_vendedor"] == user_id:
            raise HTTPException(status_code=400, detail="You cannot make an offer on your own item")

        # Include the message in the database payload
        oferta_data = {
            "importe": oferta.importe,
            "id_articulo": oferta.id_articulo,
            "id_comprador": user_id,
            "estado": "PENDIENTE",
            "mensaje": oferta.mensaje 
        }
        
        response = db.table("ofertas").insert(oferta_data).execute()
        
        if not response.data:
            raise HTTPException(status_code=400, detail="Failed to create offer")
            
        return response.data[0]
        
    except HTTPException as he:
        raise he 
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.patch("/{id_oferta}/contraoferta", response_model=OfertaResponse)
def hacer_contraoferta(
    id_oferta: str,
    contra: OfertaContra,
    db: Client = Depends(get_supabase),
    user_id: str = Depends(get_current_user)
):
    """
    Allows the buyer or seller to propose a new price and attach a new message.
    """
    try:
        oferta_res = db.table("ofertas").select("*, articulos(id_vendedor)").eq("id_oferta", id_oferta).execute()
        
        if not oferta_res.data:
            raise HTTPException(status_code=404, detail="Offer not found")
            
        oferta = oferta_res.data[0]
        
        is_buyer = oferta["id_comprador"] == user_id
        is_seller = oferta["articulos"]["id_vendedor"] == user_id
        
        if not (is_buyer or is_seller):
            raise HTTPException(status_code=403, detail="You are not part of this negotiation")
            
# 2. Check if it's valid to accept
        if oferta["estado"] not in ["PENDIENTE", "CONTRAOFERTA"]:
            raise HTTPException(status_code=400, detail="Offer cannot be accepted in its current state")
            
        # Cambiamos "DISPONIBLE" por "disponible"
        if oferta["articulos"]["estado_articulo"] != "disponible":
            raise HTTPException(status_code=400, detail="Item is no longer available")

        # 3. Reserve the Item FIRST
        db.table("articulos").update({
            "estado_articulo": "reservado" # <-- Cambiamos "RESERVADO" por "reservado"
        }).eq("id_articulo", oferta["id_articulo"]).execute()
        
        # Prepare the update payload
        update_data = {
            "importe": contra.nuevo_importe,
            "estado": "CONTRAOFERTA"
        }
        
        # If the user sends a new message, overwrite the old one
        if contra.mensaje is not None:
            update_data["mensaje"] = contra.mensaje

        update_res = db.table("ofertas").update(update_data).eq("id_oferta", id_oferta).execute()
        
        return update_res.data[0]

    except HTTPException as he:
        raise he
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))