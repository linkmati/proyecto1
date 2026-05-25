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

async def get_item_or_404(item_id: int, db: Client = Depends(get_supabase_admin)):
    """
    Esta función es para no repetir código todo el rato.
    Busca un producto y si no lo encuentra, para todo y suelta un error 404.
    """
    response = db.table("articulos").select("*").eq("id_articulo", item_id).execute()
    if not response.data:
        raise HTTPException(status_code=404, detail="Item not found")
    return response.data[0]

async def verify_item_ownership(
    item_id: int, 
    current_user_id: str = Depends(get_current_user),
    db: Client = Depends(get_supabase_admin)
):
    """
    Cuidado: aquí miramos que el que está tocando el producto sea el dueño.
    Si intentas editar algo de otro, te echa con un error 403.
    """
    item = await get_item_or_404(item_id, db)
    if item["id_vendedor"] != current_user_id:
        raise HTTPException(status_code=403, detail="You don't have permission to modify this item")
    return item

# --- Rutas de la API ---

@router.get("", response_model=List[ItemResponse])
def list_items(
    categoria: Optional[str] = None,
    search: Optional[str] = None,
    limit: int = 20,
    db: Client = Depends(get_supabase_admin)
):
    """
    Saca una lista de todos los trastos que hay a la venta.
    Puedes filtrar por categoría o buscar algo por el nombre.
    """
    try:
        # Empezamos buscando los artículos que estén disponibles (que no se hayan vendido)
        query = db.table("articulos").select("*, fotos:fotos_articulo(*), vendedor:usuarios(nombre_usuario, email)").eq("estado_articulo", "disponible")
        
        # Si nos han pasado una categoría, filtramos por ella
        if categoria and categoria != "Todas":
            query = query.eq("categoria", categoria)
            
        if search:
            # Si hay algo en el buscador, lo miramos en el título o en la descripción
            query = query.or_(f"titulo.ilike.%{search}%,descripcion.ilike.%{search}%")
            
        # Ordenamos por los más nuevos y ponemos un límite para no petar la base de datos
        response = query.order("created_at", desc=True).limit(limit).execute()
        
        # Aquí hacemos un apaño para poner el nombre del vendedor bien
        results = []
        for item in response.data:
            v_info = item.get("vendedor")
            if isinstance(v_info, list): v_info = v_info[0] if v_info else {}
            item["vendedor_nombre"] = (v_info or {}).get("nombre_usuario") or (v_info or {}).get("email", "").split("@")[0] or "Vendedor"
            results.append(item)
            
        return results
    
    except Exception as e:
        print(f"DEBUG - list_items error: {str(e)}")
        raise HTTPException(status_code=500, detail=f"Error fetching items: {str(e)}")

@router.get("/{item_id}", response_model=ItemResponse)
def get_item_details(item_id: int, db: Client = Depends(get_supabase_admin)):
    """
    Para ver toda la info de un solo producto, con sus fotos y quién lo vende.
    """
    try:
        response = db.table("articulos").select("*, fotos:fotos_articulo(*), vendedor:usuarios(nombre_usuario, email)").eq("id_articulo", item_id).execute()
        
        if not response.data:
            raise HTTPException(status_code=404, detail="Item not found")
            
        item = response.data[0]
        v_info = item.get("vendedor")
        if isinstance(v_info, list): v_info = v_info[0] if v_info else {}
        item["vendedor_nombre"] = (v_info or {}).get("nombre_usuario") or (v_info or {}).get("email", "").split("@")[0] or "Vendedor"
            
        return item
    except Exception as e:
        if isinstance(e, HTTPException): raise e
        raise HTTPException(status_code=500, detail=str(e))

@router.post("", response_model=ItemResponse)
def create_item(
    item_data: ItemCreate, 
    db: Client = Depends(get_supabase_admin),
    user_id: str = Depends(get_current_user)
):
    """
    Esto es para poner algo a la venta.
    """
    try:
        # Pasamos lo que nos llega a un diccionario y le pegamos el ID del usuario que está logueado
        new_item = item_data.model_dump()
        new_item["id_vendedor"] = user_id 
        
        response = db.table("articulos").insert(new_item).execute()
        
        if not response.data:
            raise HTTPException(status_code=400, detail="Failed to create item")
            
        # Devolvemos el producto creado, al principio no tiene fotos claro
        return {**response.data[0], "fotos": []}
    
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@router.patch("/{item_id}", response_model=ItemResponse)
async def update_item(
    item_id: int, 
    update_data: ItemUpdate,
    db: Client = Depends(get_supabase_admin),
    # ¡Aquí el Depends este ya comprueba si el usuario es el dueño! Magia.
    item: dict = Depends(verify_item_ownership)
):
    """
    Para cambiar cosas de un producto que ya hemos subido.
    """
    try:
        # Cogemos solo las cosas que han cambiado de verdad
        data_to_update = update_data.model_dump(exclude_unset=True)
        if not data_to_update:
            raise HTTPException(status_code=400, detail="No fields provided for update")

        # Guardamos los cambios
        response = db.table("articulos").update(data_to_update).eq("id_articulo", item_id).execute()
        
        # Volvemos a pillar las fotos para devolverlo todo completito
        photos_res = db.table("fotos_articulo").select("*").eq("id_articulo", item_id).execute()
        
        return {**response.data[0], "fotos": photos_res.data}
        
    except Exception as e:
        if isinstance(e, HTTPException): raise e
        raise HTTPException(status_code=500, detail=str(e))

@router.delete("/{item_id}")
async def delete_item(
    item_id: int,
    db: Client = Depends(get_supabase_admin),
    # También comprobamos aquí que seas el dueño
    item: dict = Depends(verify_item_ownership)
):
    """
    Borra un producto definitivamente de la base de datos.
    """
    try:
        # Borramos el registro físicamente
        db.table("articulos").delete().eq("id_articulo", item_id).execute()
        return {"message": f"Producto {item_id} eliminado correctamente"}
        
    except Exception as e:
        print(f"DEBUG - delete_item error: {str(e)}")
        raise HTTPException(status_code=500, detail="No se pudo eliminar el producto")

@router.post("/{item_id}/images")
async def upload_item_image(
    item_id: int,
    file: UploadFile = File(...),
    admin_db: Client = Depends(get_supabase_admin),
    # Otra vez, solo el dueño puede subir fotos de su producto
    item: dict = Depends(verify_item_ownership)
):
    """
    Para subir una foto de un producto.
    Usamos el admin_db porque el storage a veces da guerra con los permisos.
    """
    try:
        # 1. Le inventamos un nombre raro a la foto para que no se pisen
        file_extension = file.filename.split(".")[-1]
        unique_filename = f"{item_id}/{uuid.uuid4()}.{file_extension}"
        
        # 2. Leemos el archivo y lo subimos a Supabase Storage
        file_content = await file.read()
        admin_db.storage.from_("articulos-imagenes").upload(unique_filename, file_content)
        
        # 3. Pillamos el enlace público de la foto que acabamos de subir
        public_url = admin_db.storage.from_("articulos-imagenes").get_public_url(unique_filename)
        
        # 4. Guardamos ese enlace en la tabla de fotos para que sepamos que es de este producto
        admin_db.table("fotos_articulo").insert({
            "id_articulo": item_id,
            "image_url": public_url
        }).execute()
        
        return {"image_url": public_url}
        
    except Exception as e:
        print(f"IMAGE UPLOAD ERROR: {str(e)}")
        raise HTTPException(status_code=500, detail="Failed to upload image")
