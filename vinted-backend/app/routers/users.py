from fastapi import APIRouter, Depends, HTTPException
from supabase import Client
from app.db.supabase import get_supabase
from app.core.security import get_current_user
from app.models.schemas import UsuarioResponse, ArticuloResponse

router = APIRouter(prefix="/api/users", tags=["Users"])

@router.get("/me", response_model=UsuarioResponse)
def get_my_profile(
    db: Client = Depends(get_supabase),
    user_id: str = Depends(get_current_user)
):
    """
    Returns the current user's profile information.
    """
    try:
        response = db.table("usuarios").select("*").eq("id_usuario", user_id).execute()
        
        if not response.data:
            raise HTTPException(status_code=404, detail="User not found")
            
        return response.data[0]
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@router.get("/me/articulos", response_model=list[ArticuloResponse])
def get_my_articulos(
    db: Client = Depends(get_supabase),
    user_id: str = Depends(get_current_user)
):
    """
    Returns all items uploaded by the current user.
    """
    try:
        response = db.table("articulos").select("*").eq("id_vendedor", user_id).execute()
        return response.data
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))
