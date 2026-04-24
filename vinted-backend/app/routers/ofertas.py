from fastapi import APIRouter, Depends, HTTPException
from supabase import Client
from app.db.supabase import get_supabase
from app.core.security import get_current_user
from app.models.schemas import OfertaCreate, OfertaResponse, OfertaContra

router = APIRouter(prefix="/api/ofertas", tags=["Ofertas"])

@router.get("/", response_model=list[OfertaResponse])
def listar_mis_ofertas(
    db: Client = Depends(get_supabase),
    user_id: str = Depends(get_current_user)
):
    """
    Lists offers where the user is either the buyer or the seller.
    """
    try:
        # Fetch offers where user is buyer OR seller (seller requires join)
        # We can use a query with OR and join if Supabase supports it well,
        # or do two queries and merge.
        
        # Simple approach: Fetch all offers where buyer is user_id
        buyer_offers = db.table("ofertas").select("*").eq("id_comprador", user_id).execute()
        
        # Fetch articles by user_id to find offers on them
        my_articles = db.table("articulos").select("id_articulo").eq("id_vendedor", user_id).execute()
        my_art_ids = [a["id_articulo"] for a in my_articles.data]
        
        seller_offers = []
        if my_art_ids:
            seller_offers_res = db.table("ofertas").select("*").in_("id_articulo", my_art_ids).execute()
            seller_offers = seller_offers_res.data

        # Merge and remove duplicates (by id_oferta)
        all_offers_map = {o["id_oferta"]: o for o in buyer_offers.data + seller_offers}
        return list(all_offers_map.values())
        
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@router.post("/", response_model=OfertaResponse)
def crear_oferta(
    oferta: OfertaCreate, 
    db: Client = Depends(get_supabase),
    user_id: str = Depends(get_current_user)
):
    try:
        articulo_res = db.table("articulos").select("estado_articulo, id_vendedor").eq("id_articulo", oferta.id_articulo).execute()
        
        if not articulo_res.data:
            raise HTTPException(status_code=404, detail="Item not found")
            
        articulo = articulo_res.data[0]
        
        if articulo["estado_articulo"] != "disponible":
            raise HTTPException(status_code=400, detail="This item is no longer available")
             
        if articulo["id_vendedor"] == user_id:
            raise HTTPException(status_code=400, detail="You cannot make an offer on your own item")

        oferta_data = {
            "importe": oferta.importe,
            "id_articulo": oferta.id_articulo,
            "id_comprador": user_id,
            "estado": "pendiente",
            "mensaje": oferta.mensaje 
        }
        
        response = db.table("ofertas").insert(oferta_data).execute()
        
        if not response.data:
            raise HTTPException(status_code=400, detail="Failed to create offer")
            
        return response.data[0]
        
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.patch("/{id_oferta}/contraoferta", response_model=OfertaResponse)
def hacer_contraoferta(
    id_oferta: int,
    contra: OfertaContra,
    db: Client = Depends(get_supabase),
    user_id: str = Depends(get_current_user)
):
    try:
        oferta_res = db.table("ofertas").select("*, articulos(id_vendedor, estado_articulo)").eq("id_oferta", id_oferta).execute()
        
        if not oferta_res.data:
            raise HTTPException(status_code=404, detail="Offer not found")
            
        oferta = oferta_res.data[0]
        
        is_buyer = oferta["id_comprador"] == user_id
        is_seller = oferta["articulos"]["id_vendedor"] == user_id
        
        if not (is_buyer or is_seller):
            raise HTTPException(status_code=403, detail="Unauthorized")
            
        if oferta["estado"] not in ["pendiente"]:
            raise HTTPException(status_code=400, detail="Negotiation is closed")
            
        if oferta["articulos"]["estado_articulo"] != "disponible":
            raise HTTPException(status_code=400, detail="Item is no longer available")

        update_data = {
            "importe": contra.nuevo_importe,
            "mensaje": contra.mensaje if contra.mensaje else oferta["mensaje"]
        }

        update_res = db.table("ofertas").update(update_data).eq("id_oferta", id_oferta).execute()
        return update_res.data[0]

    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@router.post("/{id_oferta}/aceptar", response_model=OfertaResponse)
def aceptar_oferta(
    id_oferta: int,
    db: Client = Depends(get_supabase),
    user_id: str = Depends(get_current_user)
):
    try:
        oferta_res = db.table("ofertas").select("*, articulos(id_vendedor, estado_articulo, id_articulo)").eq("id_oferta", id_oferta).execute()
        if not oferta_res.data:
            raise HTTPException(status_code=404, detail="Offer not found")
            
        oferta = oferta_res.data[0]
        if oferta["articulos"]["id_vendedor"] != user_id:
            raise HTTPException(status_code=403, detail="Only seller can accept")
            
        if oferta["estado"] != "pendiente":
            raise HTTPException(status_code=400, detail="Offer cannot be accepted")

        if oferta["articulos"]["estado_articulo"] != "disponible":
            raise HTTPException(status_code=400, detail="Item not available")

        # Update Article to 'vendido'
        db.table("articulos").update({"estado_articulo": "vendido"}).eq("id_articulo", oferta["id_articulo"]).execute()
        
        # Update Offer to 'aceptada'
        update_res = db.table("ofertas").update({"estado": "aceptada"}).eq("id_oferta", id_oferta).execute()
        
        return update_res.data[0]
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@router.post("/{id_oferta}/rechazar", response_model=OfertaResponse)
def rechazar_oferta(
    id_oferta: int,
    db: Client = Depends(get_supabase),
    user_id: str = Depends(get_current_user)
):
    try:
        oferta_res = db.table("ofertas").select("*, articulos(id_vendedor)").eq("id_oferta", id_oferta).execute()
        if not oferta_res.data:
            raise HTTPException(status_code=404, detail="Offer not found")
            
        oferta = oferta_res.data[0]
        if user_id not in [oferta["id_comprador"], oferta["articulos"]["id_vendedor"]]:
            raise HTTPException(status_code=403, detail="Unauthorized")

        update_res = db.table("ofertas").update({"estado": "rechazada"}).eq("id_oferta", id_oferta).execute()
        return update_res.data[0]
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))
