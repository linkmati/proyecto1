from fastapi import APIRouter, Depends, HTTPException
from supabase import Client
from app.db.supabase import get_supabase, get_supabase_admin
from app.core.security import get_current_user
from app.models.schemas import FavoritoResponse

router = APIRouter(prefix="/api/favoritos", tags=["Favoritos"])

@router.post("/{id_articulo}")
def add_favorito(
    id_articulo: int,
    admin_db: Client = Depends(get_supabase_admin),
    user_id: str = Depends(get_current_user)
):
    try:
        res = admin_db.table("favoritos").upsert({
            "id_usuario": user_id,
            "id_articulo": id_articulo
        }).execute()
        return {"status": "success", "data": res.data[0]}
    except Exception as e:
        print(f"Error add_favorito: {str(e)}")
        raise HTTPException(status_code=500, detail=str(e))

@router.delete("/{id_articulo}")
def remove_favorito(
    id_articulo: int,
    admin_db: Client = Depends(get_supabase_admin),
    user_id: str = Depends(get_current_user)
):
    try:
        admin_db.table("favoritos").delete().eq("id_usuario", user_id).eq("id_articulo", id_articulo).execute()
        return {"status": "success"}
    except Exception as e:
        print(f"Error remove_favorito: {str(e)}")
        raise HTTPException(status_code=500, detail=str(e))

@router.get("/")
def list_favoritos(
    admin_db: Client = Depends(get_supabase_admin),
    user_id: str = Depends(get_current_user)
):
    try:
        # Join con admin para evitar bloqueos
        res = admin_db.table("favoritos") \
            .select("*, articulos(*, fotos:fotos_articulo(*))") \
            .eq("id_usuario", user_id) \
            .execute()
            
        return [f["articulos"] for f in res.data if f.get("articulos")]
    except Exception as e:
        print(f"Error list_favoritos: {str(e)}")
        raise HTTPException(status_code=500, detail=str(e))
