from fastapi import APIRouter, Depends, HTTPException
from supabase import Client
from app.db.supabase import get_supabase, get_supabase_admin
from app.core.security import get_current_user
from app.models.schemas import OfertaCreate, OfertaResponse, OfertaContra

router = APIRouter(prefix="/api/ofertas", tags=["Ofertas"])

@router.get("/", response_model=list[dict])
def listar_mis_ofertas(
    db: Client = Depends(get_supabase),
    user_id: str = Depends(get_current_user)
):
    """
    Lists offers with buyer info and article title.
    """
    try:
        # Traemos ofertas con join a usuarios (comprador) y articulos
        response = db.table("ofertas") \
            .select("*, usuarios!id_comprador(email), articulos(titulo, id_vendedor)") \
            .execute()
        
        all_data = []
        for o in response.data:
            is_buyer = o["id_comprador"] == user_id
            is_seller = o["articulos"]["id_vendedor"] == user_id
            
            if is_buyer or is_seller:
                o["nombre_comprador"] = o["usuarios"]["email"].split("@")[0]
                o["titulo_articulo"] = o["articulos"]["titulo"]
                all_data.append(o)
                
        return all_data
        
    except Exception as e:
        print(f"Error listing offers: {e}")
        raise HTTPException(status_code=500, detail=str(e))

@router.post("/", response_model=OfertaResponse)
def crear_oferta(
    oferta: OfertaCreate, 
    db: Client = Depends(get_supabase),
    admin_db: Client = Depends(get_supabase_admin),
    user_id: str = Depends(get_current_user)
):
    try:
        articulo_res = db.table("articulos").select("estado_articulo, id_vendedor, titulo").eq("id_articulo", oferta.id_articulo).execute()
        
        if not articulo_res.data:
            raise HTTPException(status_code=404, detail="Item not found")
            
        articulo = articulo_res.data[0]
        
        if articulo["estado_articulo"] != "disponible":
            raise HTTPException(status_code=400, detail="This item is no longer available")
             
        if articulo["id_vendedor"] == user_id:
            raise HTTPException(status_code=400, detail="No puedes hacer una oferta en tu propio artículo. Usa el botón de Contraoferta en el chat.")

        # 1. Crear la oferta
        oferta_data = {
            "importe": oferta.importe,
            "id_articulo": oferta.id_articulo,
            "id_comprador": user_id,
            "ultimo_emisor_id": user_id,
            "estado": "pendiente",
            "mensaje": oferta.mensaje 
        }
        
        response = admin_db.table("ofertas").insert(oferta_data).execute()
        
        if not response.data:
            raise HTTPException(status_code=400, detail="Failed to create offer")
            
        # 2. Enviar mensaje unificado
        try:
            u1, u2 = sorted([user_id, articulo["id_vendedor"]])
            conv_res = admin_db.table("conversaciones").select("*").eq("id_usuario_1", u1).eq("id_usuario_2", u2).eq("id_articulo", oferta.id_articulo).execute()
            
            if not conv_res.data:
                new_conv = admin_db.table("conversaciones").insert({"id_usuario_1": u1, "id_usuario_2": u2, "id_articulo": oferta.id_articulo}).execute()
                id_conv = new_conv.data[0]["id_conversacion"]
            else:
                id_conv = conv_res.data[0]["id_conversacion"]
            
            texto_final = f"He hecho una oferta de €{oferta.importe}."
            if oferta.mensaje:
                texto_final += f"\n{oferta.mensaje}"
                
            admin_db.table("mensajes").insert({
                "id_conversacion": id_conv,
                "id_emisor": user_id,
                "contenido": texto_final,
                "leido": False
            }).execute()
        except Exception as e:
            print(f"Auto-message error: {e}")
            pass 
            
        return response.data[0]
        
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@router.post("/{id_oferta}/aceptar", response_model=OfertaResponse)
def aceptar_oferta(
    id_oferta: int,
    db: Client = Depends(get_supabase),
    admin_db: Client = Depends(get_supabase_admin),
    user_id: str = Depends(get_current_user)
):
    try:
        oferta_res = db.table("ofertas").select("*, articulos(id_vendedor, estado_articulo, id_articulo, titulo)").eq("id_oferta", id_oferta).execute()
        if not oferta_res.data:
            raise HTTPException(status_code=404, detail="Offer not found")
            
        oferta = oferta_res.data[0]
        
        # Check authorization: both can accept if it's the other party's turn
        is_buyer = oferta["id_comprador"] == user_id
        is_seller = oferta["articulos"]["id_vendedor"] == user_id
        
        if not (is_buyer or is_seller):
            raise HTTPException(status_code=403, detail="No participas en esta oferta")

        if oferta["ultimo_emisor_id"] == user_id:
            raise HTTPException(status_code=400, detail="No puedes aceptar tu propia propuesta. Espera a que la otra parte responda.")
            
        if oferta["estado"] != "pendiente":
            raise HTTPException(status_code=400, detail="La oferta no está pendiente")

        # Update Article to 'vendido'
        admin_db.table("articulos").update({"estado_articulo": "vendido"}).eq("id_articulo", oferta["id_articulo"]).execute()
        
        # Update Offer to 'aceptada'
        update_res = admin_db.table("ofertas").update({"estado": "aceptada"}).eq("id_oferta", id_oferta).execute()
        
        # --- MENSAJE DE ACEPTACIÓN ---
        try:
            u1, u2 = sorted([user_id, oferta["id_comprador"] if is_seller else oferta["articulos"]["id_vendedor"]])
            conv_res = admin_db.table("conversaciones").select("id_conversacion").eq("id_usuario_1", u1).eq("id_usuario_2", u2).eq("id_articulo", oferta["id_articulo"]).execute()
            
            if conv_res.data:
                admin_db.table("mensajes").insert({
                    "id_conversacion": conv_res.data[0]["id_conversacion"],
                    "id_emisor": user_id,
                    "contenido": f"✅ ¡He aceptado la oferta! El trato se cierra por €{oferta['importe']}.",
                    "leido": False
                }).execute()
        except Exception as e:
            print(f"Accept message error: {e}")

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

@router.patch("/{id_oferta}/contraoferta", response_model=OfertaResponse)
def hacer_contraoferta(
    id_oferta: int,
    contra: OfertaContra,
    db: Client = Depends(get_supabase),
    admin_db: Client = Depends(get_supabase_admin),
    user_id: str = Depends(get_current_user)
):
    try:
        oferta_res = db.table("ofertas").select("*, articulos(id_vendedor, estado_articulo, id_articulo)").eq("id_oferta", id_oferta).execute()
        
        if not oferta_res.data:
            raise HTTPException(status_code=404, detail="Offer not found")
            
        oferta = oferta_res.data[0]
        is_buyer = oferta["id_comprador"] == user_id
        is_seller = oferta["articulos"]["id_vendedor"] == user_id
        
        if not (is_buyer or is_seller):
            raise HTTPException(status_code=403, detail="Unauthorized")

        update_data = {
            "importe": contra.nuevo_importe,
            "ultimo_emisor_id": user_id
        }
        if contra.mensaje:
            update_data["mensaje"] = contra.mensaje

        update_res = admin_db.table("ofertas").update(update_data).eq("id_oferta", id_oferta).execute()
        
        # --- MENSAJE DE CONTRAOFERTA ---
        try:
            texto = f"He hecho una contraoferta de €{contra.nuevo_importe}."
            if contra.mensaje: texto += f"\n{contra.mensaje}"
            
            u1, u2 = sorted([oferta["id_comprador"], oferta["articulos"]["id_vendedor"]])
            conv_res = admin_db.table("conversaciones").select("id_conversacion").eq("id_usuario_1", u1).eq("id_usuario_2", u2).eq("id_articulo", oferta["id_articulo"]).execute()
            
            if conv_res.data:
                admin_db.table("mensajes").insert({
                    "id_conversacion": conv_res.data[0]["id_conversacion"],
                    "id_emisor": user_id,
                    "contenido": texto,
                    "leido": False
                }).execute()
        except Exception as e:
            print(f"Contra-message error: {e}")

        return update_res.data[0]

    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))
