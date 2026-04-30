from fastapi import APIRouter, Depends, HTTPException, UploadFile, File
from supabase import Client
import uuid
from app.db.supabase import get_supabase, get_supabase_admin
from app.models.schemas import ArticuloCreate, ArticuloResponse, ArticuloUpdate
from app.core.security import get_current_user

router = APIRouter(
    prefix="/api/articulos",
    tags=["Articulos"]
)

@router.post("/{id_articulo}/imagenes")
async def upload_articulo_imagen(
    id_articulo: int,
    file: UploadFile = File(...),
    db: Client = Depends(get_supabase),
    admin_db: Client = Depends(get_supabase_admin),
    user_id: str = Depends(get_current_user)
):
    """
    Uploads an image using ADMIN client to bypass storage RLS.
    """
    try:
        # 1. Check ownership (using normal db is fine for SELECT)
        check_res = db.table("articulos").select("id_vendedor").eq("id_articulo", id_articulo).execute()
        if not check_res.data:
            raise HTTPException(status_code=404, detail="Item not found")
        if check_res.data[0]["id_vendedor"] != user_id:
            raise HTTPException(status_code=403, detail="Unauthorized")

        # 2. Upload to Storage using ADMIN client
        file_ext = file.filename.split(".")[-1]
        file_path = f"{id_articulo}/{uuid.uuid4()}.{file_ext}"
        contents = await file.read()
        
        # We use admin_db here
        admin_db.storage.from_("articulos-imagenes").upload(file_path, contents)
        
        # 3. Get Public URL
        public_url = admin_db.storage.from_("articulos-imagenes").get_public_url(file_path)
        
        # 4. Insert into 'fotos_articulo' (using admin_db to be safe)
        admin_db.table("fotos_articulo").insert({
            "id_articulo": id_articulo,
            "image_url": public_url
        }).execute()
        
        return {"url": public_url}
        
    except Exception as e:
        print(f"Upload error: {str(e)}")
        raise HTTPException(status_code=500, detail=str(e))

@router.post("/", response_model=ArticuloResponse)
def create_articulo(
    articulo: ArticuloCreate, 
    db: Client = Depends(get_supabase),
    user_id: str = Depends(get_current_user)
):
    try:
        item_data = articulo.model_dump()
        item_data["id_vendedor"] = user_id 
        
        response = db.table("articulos").insert(item_data).execute()
        
        if not response.data:
            raise HTTPException(status_code=400, detail="Failed to create item")
            
        return {**response.data[0], "fotos": []}
    
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@router.get("/", response_model=list[ArticuloResponse])
def list_articulos(
    categoria: Optional[str] = None,
    search: Optional[str] = None,
    limit: int = 20,
    db: Client = Depends(get_supabase)
):
    """
    Fetches latest available items with their photos. Supports category filter and text search.
    """
    try:
        query = db.table("articulos").select("*, fotos:fotos_articulo(*)").eq("estado_articulo", "disponible")
        
        if categoria and categoria != "Todas":
            query = query.eq("categoria", categoria)
            
        if search:
            # Búsqueda en título o descripción usando or con ilike
            query = query.or_(f"titulo.ilike.%{search}%,descripcion.ilike.%{search}%")
            
        response = query.order("created_at", desc=True).limit(limit).execute()
        return response.data
    
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@router.get("/{id_articulo}", response_model=ArticuloResponse)
def get_articulo(id_articulo: int, db: Client = Depends(get_supabase)):
    """
    Fetches a single item with its photos.
    """
    try:
        response = db.table("articulos").select("*, fotos:fotos_articulo(*)").eq("id_articulo", id_articulo).execute()
        
        if not response.data:
            raise HTTPException(status_code=404, detail="Item not found")
            
        return response.data[0]
    except HTTPException as he:
        raise he
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@router.patch("/{id_articulo}", response_model=ArticuloResponse)
def update_articulo(
    id_articulo: int, 
    articulo_update: ArticuloUpdate,
    db: Client = Depends(get_supabase),
    user_id: str = Depends(get_current_user)
):
    try:
        check_res = db.table("articulos").select("id_vendedor").eq("id_articulo", id_articulo).execute()
        if not check_res.data:
            raise HTTPException(status_code=404, detail="Item not found")
        
        if check_res.data[0]["id_vendedor"] != user_id:
            raise HTTPException(status_code=403, detail="Unauthorized")

        update_data = articulo_update.model_dump(exclude_unset=True)
        if not update_data:
            raise HTTPException(status_code=400, detail="No fields to update")

        response = db.table("articulos").update(update_data).eq("id_articulo", id_articulo).execute()
        
        # Fetch fotos to return complete response
        fotos_res = db.table("fotos_articulo").select("*").eq("id_articulo", id_articulo).execute()
        
        return {**response.data[0], "fotos": fotos_res.data}
        
    except HTTPException as he:
        raise he
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@router.delete("/{id_articulo}")
def delete_articulo(
    id_articulo: int,
    db: Client = Depends(get_supabase),
    user_id: str = Depends(get_current_user)
):
    try:
        check_res = db.table("articulos").select("id_vendedor").eq("id_articulo", id_articulo).execute()
        if not check_res.data:
            raise HTTPException(status_code=404, detail="Item not found")
        
        if check_res.data[0]["id_vendedor"] != user_id:
            raise HTTPException(status_code=403, detail="Unauthorized")

        db.table("articulos").update({"estado_articulo": "desactivado"}).eq("id_articulo", id_articulo).execute()
        
        return {"message": "Item successfully deactivated"}
        
    except HTTPException as he:
        raise he
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))
