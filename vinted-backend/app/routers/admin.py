from fastapi import APIRouter, Depends, HTTPException
from supabase import Client
from typing import List, Optional
from app.db.supabase import get_supabase
from app.core.security import get_admin_user
from app.models.schemas import ItemResponse, UserResponse, OfferResponse

router = APIRouter(prefix="/api/admin", tags=["Admin"])

# --- Products Management ---

@router.get("/items", response_model=List[ItemResponse])
def get_all_items(
    db: Client = Depends(get_supabase),
    admin_id: str = Depends(get_admin_user),
    search: Optional[str] = None
):
    """
    Returns all items in the platform. Supports optional search by title.
    """
    try:
        query = db.table("articulos").select("*, fotos:fotos_articulo(*)")
        if search:
            query = query.ilike("titulo", f"%{search}%")
        
        response = query.order("created_at", desc=True).execute()
        return response.data
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@router.delete("/items/{item_id}")
def delete_item(
    item_id: int,
    db: Client = Depends(get_supabase),
    admin_id: str = Depends(get_admin_user)
):
    """
    Deletes an item from the platform.
    """
    try:
        db.table("articulos").delete().eq("id_articulo", item_id).execute()
        return {"message": f"Item {item_id} deleted successfully"}
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

# --- Users Management ---

@router.get("/users", response_model=List[UserResponse])
def get_all_users(
    db: Client = Depends(get_supabase),
    admin_id: str = Depends(get_admin_user),
    search: Optional[str] = None
):
    """
    Returns all registered users.
    """
    try:
        query = db.table("usuarios").select("*")
        if search:
            query = query.ilike("email", f"%{search}%")
            
        response = query.order("created_at", desc=True).execute()
        return response.data
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@router.patch("/users/{user_id}/suspend")
def suspend_user(
    user_id: str,
    db: Client = Depends(get_supabase),
    admin_id: str = Depends(get_admin_user)
):
    """
    Suspends a user account.
    """
    try:
        db.table("usuarios").update({"estado": "suspendido"}).eq("id_usuario", user_id).execute()
        return {"message": f"User {user_id} suspended"}
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@router.delete("/users/{user_id}")
def delete_user(
    user_id: str,
    db: Client = Depends(get_supabase),
    admin_id: str = Depends(get_admin_user)
):
    """
    Deletes a user account. Note: This only deletes from our 'usuarios' table.
    Deleting from Supabase Auth requires admin client and usually handled via dashboard or separate logic.
    """
    try:
        db.table("usuarios").delete().eq("id_usuario", user_id).execute()
        return {"message": f"User {user_id} deleted from profile table"}
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

# --- Offers Management ---

@router.get("/offers", response_model=List[OfferResponse])
def get_all_offers(
    db: Client = Depends(get_supabase),
    admin_id: str = Depends(get_admin_user)
):
    """
    Returns all offers.
    """
    try:
        response = db.table("ofertas").select("*").order("created_at", desc=True).execute()
        return response.data
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@router.delete("/offers/{offer_id}")
def delete_offer(
    offer_id: int,
    db: Client = Depends(get_supabase),
    admin_id: str = Depends(get_admin_user)
):
    """
    Deletes an offer.
    """
    try:
        db.table("ofertas").delete().eq("id_oferta", offer_id).execute()
        return {"message": f"Offer {offer_id} deleted"}
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))
