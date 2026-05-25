from fastapi import APIRouter, Depends, HTTPException
from supabase import Client
from typing import List, Optional
from app.db.supabase import get_supabase, get_supabase_admin
from app.core.security import get_admin_user
from app.models.schemas import ItemResponse, UserResponse, OfferResponse, ItemUpdate

router = APIRouter(prefix="/api/admin", tags=["Admin"])

# --- Gestión de Productos (Cosas de Admin) ---

@router.get("/items", response_model=List[ItemResponse])
def get_all_items(
    db: Client = Depends(get_supabase_admin),
    admin_id: str = Depends(get_admin_user),
    search: Optional[str] = None
):
    """
    Saca absolutamente todos los productos que hay en la app. 
    Puedes buscar por el título si quieres encontrar algo rápido.
    """
    try:
        # Buscamos los productos, sus fotos y quién los vende
        query = db.table("articulos").select("*, fotos:fotos_articulo(*), vendedor:usuarios(nombre_usuario, email)")
        if search:
            query = query.ilike("titulo", f"%{search}%")
        
        response = query.order("created_at", desc=True).execute()
        
        # Apañamos los nombres de los vendedores para que queden bien
        results = []
        for item in response.data:
            v_info = item.get("vendedor")
            if isinstance(v_info, list): v_info = v_info[0] if v_info else {}
            item["vendedor_nombre"] = (v_info or {}).get("nombre_usuario") or (v_info or {}).get("email", "").split("@")[0] or "Vendedor"
            results.append(item)
            
        return results
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@router.delete("/items/{item_id}")
def delete_item(
    item_id: int,
    db: Client = Depends(get_supabase_admin),
    admin_id: str = Depends(get_admin_user)
):
    """
    Para borrar un producto de la app para siempre.
    """
    try:
        db.table("articulos").delete().eq("id_articulo", item_id).execute()
        return {"message": f"Item {item_id} deleted successfully"}
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@router.patch("/items/{item_id}/category")
def update_item_category(
    item_id: int,
    item_data: ItemUpdate,
    db: Client = Depends(get_supabase_admin),
    admin_id: str = Depends(get_admin_user)
):
    """
    Para cambiarle la categoría a un producto (por si el usuario se ha equivocado).
    """
    try:
        if not item_data.categoria:
            raise HTTPException(status_code=400, detail="Category is required")
            
        db.table("articulos").update({"categoria": item_data.categoria}).eq("id_articulo", item_id).execute()
        return {"message": f"Category of item {item_id} updated to {item_data.categoria}"}
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

# --- Gestión de Usuarios ---

@router.get("/users", response_model=List[UserResponse])
def get_all_users(
    db: Client = Depends(get_supabase_admin),
    admin_id: str = Depends(get_admin_user),
    search: Optional[str] = None
):
    """
    Saca la lista de toda la gente que se ha registrado.
    """
    try:
        query = db.table("usuarios").select("*")
        if search:
            query = query.ilike("email", f"%{search}%")
            
        response = query.order("created_at", desc=True).execute()
        print(f"DEBUG - Admin get_all_users: Found {len(response.data)} users")
        return response.data
    except Exception as e:
        print(f"DEBUG - Admin get_all_users error: {str(e)}")
        raise HTTPException(status_code=500, detail=str(e))

@router.patch("/users/{user_id}/suspend")
def suspend_user(
    user_id: str,
    db: Client = Depends(get_supabase_admin),
    admin_id: str = Depends(get_admin_user)
):
    """
    Para banear a un usuario. Le pone el estado en 'suspendido'.
    """
    try:
        db.table("usuarios").update({"estado": "suspendido"}).eq("id_usuario", user_id).execute()
        return {"message": f"User {user_id} suspended"}
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@router.patch("/users/{user_id}/reactivate")
def reactivate_user(
    user_id: str,
    db: Client = Depends(get_supabase_admin),
    admin_id: str = Depends(get_admin_user)
):
    """
    Para quitarle el baneo a un usuario. Vuelve a estar 'activo'.
    """
    try:
        db.table("usuarios").update({"estado": "activo"}).eq("id_usuario", user_id).execute()
        return {"message": f"User {user_id} reactivated"}
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@router.delete("/users/{user_id}")
def delete_user(
    user_id: str,
    db: Client = Depends(get_supabase_admin),
    admin_id: str = Depends(get_admin_user)
):
    """
    Borra a un usuario de nuestra tabla. 
    Ojo, que en Supabase Auth todavía seguirá estando, pero aquí ya no.
    """
    try:
        db.table("usuarios").delete().eq("id_usuario", user_id).execute()
        return {"message": f"User {user_id} deleted from profile table"}
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

# --- Gestión de Ofertas ---

@router.get("/offers", response_model=List[OfferResponse])
def get_all_offers(
    db: Client = Depends(get_supabase_admin),
    admin_id: str = Depends(get_admin_user)
):
    """
    Saca todas las ofertas que se han hecho en la app.
    """
    try:
        response = db.table("ofertas").select("*, articulos(titulo)").order("created_at", desc=True).execute()
        
        results = []
        for offer in response.data:
            art = offer.get("articulos")
            if isinstance(art, list): art = art[0] if art else {}
            offer["articulo_titulo"] = (art or {}).get("titulo", "Artículo no disponible")
            results.append(offer)
            
        return results
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@router.delete("/offers/{offer_id}")
def delete_offer(
    offer_id: int,
    db: Client = Depends(get_supabase_admin),
    admin_id: str = Depends(get_admin_user)
):
    """
    Para borrar una oferta.
    """
    try:
        db.table("ofertas").delete().eq("id_oferta", offer_id).execute()
        return {"message": f"Offer {offer_id} deleted"}
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))
