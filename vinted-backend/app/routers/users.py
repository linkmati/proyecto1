from fastapi import APIRouter, Depends, HTTPException
from supabase import Client
from typing import List
from app.db.supabase import get_supabase, get_supabase_admin
from app.core.security import get_current_user
from app.models.schemas import UserResponse, ItemResponse, OrderResponse

router = APIRouter(prefix="/api/users", tags=["Users"])

@router.get("/me", response_model=UserResponse)
def get_my_profile(
    db: Client = Depends(get_supabase_admin),
    user_id: str = Depends(get_current_user)
):
    """
    Saca los datos de mi perfil (el que está logueado ahora mismo).
    """
    try:
        response = db.table("usuarios").select("*").eq("id_usuario", user_id).execute()
        
        if not response.data:
            raise HTTPException(status_code=404, detail="User profile not found")
            
        return response.data[0]
    except Exception as e:
        if isinstance(e, HTTPException): raise e
        print(f"DEBUG - get_my_profile error: {str(e)}")
        raise HTTPException(status_code=500, detail=f"Error fetching profile: {str(e)}")

@router.get("/me/items", response_model=List[ItemResponse])
def get_my_items(
    db: Client = Depends(get_supabase_admin),
    user_id: str = Depends(get_current_user)
):
    """
    Saca todos los trastos que yo he puesto a la venta.
    """
    try:
        response = db.table("articulos").select("*, fotos:fotos_articulo(*)").eq("id_vendedor", user_id).execute()
        return response.data
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error fetching your items: {str(e)}")

@router.get("/me/favorites", response_model=List[ItemResponse])
def get_my_favorited_items(
    db: Client = Depends(get_supabase_admin),
    user_id: str = Depends(get_current_user)
):
    """
    Te da la lista completa de las cosas que te han gustado.
    """
    try:
        response = db.table("favoritos") \
            .select("id_articulo, articulos(*, fotos:fotos_articulo(*))") \
            .eq("id_usuario", user_id) \
            .execute()
            
        # Limpiamos los datos para que solo salgan los productos y no el lío de la tabla de favoritos
        favorited_items = []
        for fav in response.data:
            if fav.get("articulos"):
                item = fav["articulos"]
                # A veces Supabase devuelve una lista en vez de un objeto, así que lo arreglamos
                if isinstance(item, list): item = item[0] if item else None
                if item: favorited_items.append(item)
                
        return favorited_items
    except Exception as e:
        print(f"DEBUG - get_my_favorited_items error: {str(e)}")
        raise HTTPException(status_code=500, detail="Error fetching favorited items")

@router.get("/me/purchases", response_model=List[OrderResponse])
def get_my_purchases(
    db: Client = Depends(get_supabase_admin),
    user_id: str = Depends(get_current_user)
):
    """
    Muestra todo lo que has comprado. 
    También mete aquí las ofertas que te han aceptado, por si todavía no se ha creado el pedido de verdad.
    """
    try:
        # 1. Miramos en la tabla de 'pedidos'
        response = db.table("pedidos").select("*, articulo:articulos(*, fotos:fotos_articulo(*))").eq("id_comprador", user_id).execute()
        
        purchases = []
        purchased_item_ids = set()
        for order in response.data:
            if order.get("articulo"):
                item = order["articulo"]
                if isinstance(item, list): item = item[0] if item else None
                order["articulo"] = item
                if item: purchased_item_ids.add(item["id_articulo"])
            purchases.append(order)
            
        # 2. Miramos en 'ofertas' las que ya están aceptadas
        ofertas_res = db.table("ofertas").select("*, articulo:articulos(*, fotos:fotos_articulo(*))").eq("id_comprador", user_id).eq("estado", "aceptada").execute()
        for offer in ofertas_res.data:
            if offer["id_articulo"] in purchased_item_ids:
                continue # Si ya está en pedidos, no lo repetimos
                
            item = offer.get("articulo")
            if isinstance(item, list): item = item[0] if item else None
            
            # Hacemos que la oferta parezca un pedido para que el frontend no se entere
            pseudo_order = {
                "id_pedido": offer["id_oferta"], # Usamos el ID de la oferta de parche
                "id_comprador": offer["id_comprador"],
                "id_articulo": offer["id_articulo"],
                "estado_pedido": "completado", 
                "precio_final": offer["importe"],
                "created_at": offer["created_at"],
                "articulo": item
            }
            purchases.append(pseudo_order)
            
        return purchases
    except Exception as e:
        print(f"DEBUG - get_my_purchases error: {str(e)}")
        raise HTTPException(status_code=500, detail=f"Error fetching your purchases: {str(e)}")
