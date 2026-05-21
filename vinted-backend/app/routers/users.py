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
    Returns all items that the current user has listed for sale.
    """
    try:
        response = db.table("articulos").select("*, fotos:fotos_articulo(*)").eq("id_vendedor", user_id).execute()
        return response.data
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error fetching your items: {str(e)}")

@router.get("/me/purchases", response_model=List[OrderResponse])
def get_my_purchases(
    db: Client = Depends(get_supabase_admin),
    user_id: str = Depends(get_current_user)
):
    """
    Returns all successful purchases (orders) made by the current user.
    """
    try:
        response = db.table("pedidos").select("*").eq("id_comprador", user_id).execute()
        return response.data
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error fetching your purchases: {str(e)}")
