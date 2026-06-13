from fastapi import APIRouter, Depends, HTTPException, UploadFile, File
import uuid
from typing import Optional, List
from app.db.supabase import get_supabase_admin, get_db_connection
from app.models.schemas import ItemCreate, ItemResponse, ItemUpdate
from app.core.security import get_current_user

router = APIRouter(prefix="/api/items", tags=["Items"])

# --- FUNCIONES PARA NO REPETIR ---

async def buscar_producto(id: int, conn):
    """Busca un producto. Si no está, falla."""
    with conn.cursor() as cur:
        # NOTA PRESENTACIÓN: Siempre pasamos las variables como tupla `(id,)` 
        # en lugar de concatenar cadenas tipo f"SELECT ... {id}".
        # Esto previene ataques de Inyección SQL.
        cur.execute("SELECT * FROM articulos WHERE id_articulo = %s", (id,))
        item = cur.fetchone()
    if not item:
        raise HTTPException(404, "No existe este producto")
    return item

async def soy_el_dueño(id: int, user_id: str, conn):
    """Mira si el usuario es el que vende el producto."""
    item = await buscar_producto(id, conn)
    if str(item["id_vendedor"]) != user_id:
        raise HTTPException(403, "No es tu producto, no puedes tocarlo")
    return item

# --- RUTAS ---

@router.get("", response_model=List[ItemResponse])
def ver_todo(
    categoria: Optional[str] = None,
    search: Optional[str] = None,
    limit: int = 20,
    conn = Depends(get_db_connection)
):
    """Muestra los productos en venta."""
    # SQL muy básico
    consulta = "SELECT * FROM articulos WHERE estado_articulo = 'disponible'"
    parametros = []
    
    # NOTA PRESENTACIÓN: Montamos la consulta dinámicamente según lo que pida el usuario
    if categoria and categoria != "Todas":
        consulta += " AND categoria = %s"
        parametros.append(categoria)
        
    if search:
        # Usamos LOWER para que no importen las mayúsculas (búsqueda fácil)
        consulta += " AND (LOWER(titulo) LIKE LOWER(%s) OR LOWER(descripcion) LIKE LOWER(%s))"
        texto = f"%{search}%"
        parametros.extend([texto, texto])
        
    consulta += " ORDER BY created_at DESC LIMIT %s"
    parametros.append(limit)
    
    with conn.cursor() as cur:
        cur.execute(consulta, tuple(parametros))
        lista = cur.fetchall()
        
        # Rellenamos lo que falta (fotos y nombre del vendedor)
        for p in lista:
            cur.execute("SELECT * FROM fotos_articulo WHERE id_articulo = %s", (p["id_articulo"],))
            p["fotos"] = cur.fetchall()
            
            cur.execute("SELECT nombre_usuario, email FROM usuarios WHERE id_usuario = %s", (p["id_vendedor"],))
            vendedor = cur.fetchone()
            if vendedor:
                p["vendedor_nombre"] = vendedor["nombre_usuario"] or vendedor["email"].split("@")[0]
            else:
                p["vendedor_nombre"] = "Vendedor"
            
    return lista

@router.get("/{id}", response_model=ItemResponse)
def ver_uno(id: int, conn = Depends(get_db_connection)):
    """Pilla toda la info de un solo trasto."""
    with conn.cursor() as cur:
        cur.execute("SELECT * FROM articulos WHERE id_articulo = %s", (id,))
        item = cur.fetchone()
        if not item: raise HTTPException(404, "No encontrado")
        
        # Fotos
        cur.execute("SELECT * FROM fotos_articulo WHERE id_articulo = %s", (id,))
        item["fotos"] = cur.fetchall()
        
        # Vendedor
        cur.execute("SELECT nombre_usuario, email FROM usuarios WHERE id_usuario = %s", (item["id_vendedor"],))
        v = cur.fetchone()
        item["vendedor_nombre"] = (v["nombre_usuario"] or v["email"].split("@")[0]) if v else "Vendedor"
        
    return item

@router.post("", response_model=ItemResponse)
def crear(datos: ItemCreate, conn = Depends(get_db_connection), user_id: str = Depends(get_current_user)):
    """Añade un producto a la base de datos."""
    item = datos.model_dump()
    item["id_vendedor"] = user_id 
    
    # NOTA PRESENTACIÓN: Montamos el INSERT generando los nombres de las columnas y los %s
    # automáticamente en base a las claves del diccionario que nos llega del frontend.
    columnas = ", ".join(item.keys())
    valores = ", ".join(["%s"] * len(item))
    sql = f"INSERT INTO articulos ({columnas}) VALUES ({valores}) RETURNING *"
    
    try:
        with conn.cursor() as cur:
            cur.execute(sql, list(item.values()))
            nuevo = cur.fetchone()
            # NOTA PRESENTACIÓN: Hacer commit es fundamental para confirmar la transacción.
            # Si no, se queda en el limbo y no se guarda en disco.
            conn.commit()
            return {**nuevo, "fotos": []}
    except Exception as e:
        conn.rollback()
        raise HTTPException(500, "Fallo al guardar en la base de datos")

@router.patch("/{id}", response_model=ItemResponse)
async def editar(id: int, datos: ItemUpdate, conn = Depends(get_db_connection), user_id: str = Depends(get_current_user)):
    """Cambia datos de un producto tuyo."""
    await soy_el_dueño(id, user_id, conn)
    
    # Solo lo que haya cambiado
    dict_datos = datos.model_dump(exclude_unset=True)
    if not dict_datos: raise HTTPException(400, "Nada que cambiar")

    sets = ", ".join([f"{c} = %s" for c in dict_datos.keys()])
    sql = f"UPDATE articulos SET {sets} WHERE id_articulo = %s RETURNING *"
    params = list(dict_datos.values()) + [id]
    
    try:
        with conn.cursor() as cur:
            cur.execute(sql, params)
            editado = cur.fetchone()
            # Fotos para que no se pierdan en el frontend
            cur.execute("SELECT * FROM fotos_articulo WHERE id_articulo = %s", (id,))
            editado["fotos"] = cur.fetchall()
            conn.commit()
            return editado
    except Exception as e:
        conn.rollback()
        raise HTTPException(500, "Fallo al actualizar")

@router.delete("/{id}")
async def borrar(id: int, conn = Depends(get_db_connection), user_id: str = Depends(get_current_user)):
    """Elimina el producto para siempre."""
    await soy_el_dueño(id, user_id, conn)
    try:
        with conn.cursor() as cur:
            cur.execute("DELETE FROM articulos WHERE id_articulo = %s", (id,))
            conn.commit()
        return {"message": "Borrado OK"}
    except Exception:
        conn.rollback()
        raise HTTPException(500, "No se ha podido borrar")

@router.post("/{id}/images")
async def subir_foto(id: int, file: UploadFile = File(...), admin_db = Depends(get_supabase_admin), conn = Depends(get_db_connection), user_id: str = Depends(get_current_user)):
    """Sube la foto y guarda el link."""
    await soy_el_dueño(id, user_id, conn)
    try:
        nombre = f"{id}/{uuid.uuid4()}.{file.filename.split('.')[-1]}"
        admin_db.storage.from_("articulos-imagenes").upload(nombre, await file.read())
        url = admin_db.storage.from_("articulos-imagenes").get_public_url(nombre)
        
        with conn.cursor() as cur:
            cur.execute("INSERT INTO fotos_articulo (id_articulo, image_url) VALUES (%s, %s)", (id, url))
            conn.commit()
        return {"image_url": url}
    except Exception:
        conn.rollback()
        raise HTTPException(500, "Error con la foto")
