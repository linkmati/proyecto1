from fastapi import APIRouter, Depends, HTTPException, UploadFile, File
from supabase import Client
import uuid
from typing import Optional, List
from app.db.supabase import get_supabase, get_supabase_admin
from app.models.schemas import ItemCreate, ItemResponse, ItemUpdate
from app.core.security import get_current_user

router = APIRouter(
    prefix="/api/items",
    tags=["Items"]
)

async def get_item_or_404(item_id: int, db: Client = Depends(get_supabase)):
    """
    Helper function to fetch an item and ensure it exists.
    If it doesn't exist, it stops the request and returns a 404 error.
    """
    response = db.table("articulos").select("*").eq("id_articulo", item_id).execute()
    if not response.data:
        raise HTTPException(status_code=404, detail="Item not found")
    return response.data[0]

async def verify_item_ownership(
    item_id: int, 
    current_user_id: str = Depends(get_current_user),
    db: Client = Depends(get_supabase)
):
    """
    Security check: Ensures the logged-in user is the owner of the item.
    Reuses 'get_item_or_404' logic implicitly by checking the result.
    """
    item = await get_item_or_404(item_id, db)
    if item["id_vendedor"] != current_user_id:
        raise HTTPException(status_code=403, detail="You don't have permission to modify this item")
    return item

# --- API Routes ---

@router.get("", response_model=List[ItemResponse])
def list_items(
    category: Optional[str] = None,
    search: Optional[str] = None,
    limit: int = 20,
    db: Client = Depends(get_supabase)
):
    """
    Returns a list of available items. 
    Can be filtered by category or search text.
    """
    try:
        # Start the query selecting items and their related photos
        query = db.table("articulos").select("*, fotos:fotos_articulo(*)").eq("estado_articulo", "disponible")
        
        # Apply filters if provided
        if category and category != "Todas":
            query = query.eq("categoria", category)
            
        if search:
            # Look for matches in title OR description
            query = query.or_(f"titulo.ilike.%{search}%,descripcion.ilike.%{search}%")
            
        # Execute query with sorting and limit
        response = query.order("created_at", desc=True).limit(limit).execute()
        return response.data
    
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error fetching items: {str(e)}")

@router.get("/{item_id}", response_model=ItemResponse)
def get_item_details(item_id: int, db: Client = Depends(get_supabase)):
    """
    Returns full details for a single item, including its photos.
    """
    try:
        response = db.table("articulos").select("*, fotos:fotos_articulo(*)").eq("id_articulo", item_id).execute()
        
        if not response.data:
            raise HTTPException(status_code=404, detail="Item not found")
            
        return response.data[0]
    except Exception as e:
        if isinstance(e, HTTPException): raise e
        raise HTTPException(status_code=500, detail=str(e))

@router.post("/", response_model=ItemResponse)
def create_item(
    item_data: ItemCreate, 
    db: Client = Depends(get_supabase),
    user_id: str = Depends(get_current_user)
):
    """
    Creates a new item listing for the logged-in user.
    """
    try:
        # Convert Pydantic model to a Python dictionary and add the seller ID
        new_item = item_data.model_dump()
        new_item["id_vendedor"] = user_id 
        
        response = db.table("articulos").insert(new_item).execute()
        
        if not response.data:
            raise HTTPException(status_code=400, detail="Failed to create item")
            
        # Return the created item with an empty list for photos
        return {**response.data[0], "fotos": []}
    
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@router.patch("/{item_id}", response_model=ItemResponse)
async def update_item(
    item_id: int, 
    update_data: ItemUpdate,
    db: Client = Depends(get_supabase),
    # This dependency automatically checks if the user owns the item!
    item: dict = Depends(verify_item_ownership)
):
    """
    Updates an existing item's information.
    """
    try:
        # Get only the fields that were actually provided in the request
        data_to_update = update_data.model_dump(exclude_unset=True)
        if not data_to_update:
            raise HTTPException(status_code=400, detail="No fields provided for update")

        # Perform the update
        response = db.table("articulos").update(data_to_update).eq("id_articulo", item_id).execute()
        
        # Fetch current photos to return a complete response object
        photos_res = db.table("fotos_articulo").select("*").eq("id_articulo", item_id).execute()
        
        return {**response.data[0], "fotos": photos_res.data}
        
    except Exception as e:
        if isinstance(e, HTTPException): raise e
        raise HTTPException(status_code=500, detail=str(e))

@router.delete("/{item_id}")
async def deactivate_item(
    item_id: int,
    db: Client = Depends(get_supabase),
    # Security check included here
    item: dict = Depends(verify_item_ownership)
):
    """
    Soft-deletes an item by changing its status to 'desactivado'.
    """
    try:
        db.table("articulos").update({"estado_articulo": "desactivado"}).eq("id_articulo", item_id).execute()
        return {"message": f"Item {item_id} has been deactivated successfully"}
        
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@router.post("/{item_id}/images")
async def upload_item_image(
    item_id: int,
    file: UploadFile = File(...),
    admin_db: Client = Depends(get_supabase_admin),
    # Security check: only the owner can upload images
    item: dict = Depends(verify_item_ownership)
):
    """
    Uploads an image for a specific item.
    Uses the Admin client to handle storage permissions easily.
    """
    try:
        # 1. Generate a unique name for the file
        file_extension = file.filename.split(".")[-1]
        unique_filename = f"{item_id}/{uuid.uuid4()}.{file_extension}"
        
        # 2. Read file content and upload to Supabase Storage
        file_content = await file.read()
        admin_db.storage.from_("articulos-imagenes").upload(unique_filename, file_content)
        
        # 3. Get the public URL for the uploaded image
        public_url = admin_db.storage.from_("articulos-imagenes").get_public_url(unique_filename)
        
        # 4. Link the photo to the item in the database
        admin_db.table("fotos_articulo").insert({
            "id_articulo": item_id,
            "image_url": public_url
        }).execute()
        
        return {"image_url": public_url}
        
    except Exception as e:
        print(f"IMAGE UPLOAD ERROR: {str(e)}")
        raise HTTPException(status_code=500, detail="Failed to upload image")
