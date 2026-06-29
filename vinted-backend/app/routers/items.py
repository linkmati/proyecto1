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
    # NOTA PRESENTACIÓN: [SQL_INJECTION_PREVENTION] Uso de parámetros en tupla para evitar vulnerabilidades de Inyección SQL.
    cursor = conn.cursor()
    query = "SELECT * FROM articulos WHERE id_articulo = %s"
    cursor.execute(query, (id,))
    item = cursor.fetchone()
    cursor.close()
    
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
    query = "SELECT * FROM articulos WHERE estado_articulo = 'disponible'"
    parametros = []
    
    # NOTA PRESENTACIÓN: [DYNAMIC_FILTERING] Construcción dinámica de consulta SQL según parámetros recibidos.
    if categoria and categoria != "Todas":
        query += " AND categoria = %s"
        parametros.append(categoria)
        
    if search:
        # Usamos LOWER para que no importen las mayúsculas (búsqueda fácil)
        query += " AND (LOWER(titulo) LIKE LOWER(%s) OR LOWER(descripcion) LIKE LOWER(%s))"
        texto = f"%{search}%"
        parametros.extend([texto, texto])
        
    query += " ORDER BY created_at DESC LIMIT %s"
    parametros.append(limit)
    
    cursor = conn.cursor()
    cursor.execute(query, tuple(parametros))
    lista = cursor.fetchall()
    
    # Rellenamos lo que falta (fotos y nombre del vendedor)
    for p in lista:
        query_fotos = "SELECT * FROM fotos_articulo WHERE id_articulo = %s"
        cursor.execute(query_fotos, (p["id_articulo"],))
        p["fotos"] = cursor.fetchall()
        
        query_vendedor = "SELECT nombre_usuario, email FROM usuarios WHERE id_usuario = %s"
        cursor.execute(query_vendedor, (p["id_vendedor"],))
        vendedor = cursor.fetchone()
        if vendedor:
            p["vendedor_nombre"] = vendedor["nombre_usuario"] or vendedor["email"].split("@")[0]
        else:
            p["vendedor_nombre"] = "Vendedor"
            
    cursor.close()
    return lista

@router.get("/{id}", response_model=ItemResponse)
def ver_uno(id: int, conn = Depends(get_db_connection)):
    """Pilla toda la info de un solo trasto."""
    cursor = conn.cursor()
    query = "SELECT * FROM articulos WHERE id_articulo = %s"
    cursor.execute(query, (id,))
    item = cursor.fetchone()
    
    if not item: 
        cursor.close()
        raise HTTPException(404, "No encontrado")
    
    # Fotos
    query_fotos = "SELECT * FROM fotos_articulo WHERE id_articulo = %s"
    cursor.execute(query_fotos, (id,))
    item["fotos"] = cursor.fetchall()
    
    # Vendedor
    query_vendedor = "SELECT nombre_usuario, email FROM usuarios WHERE id_usuario = %s"
    cursor.execute(query_vendedor, (item["id_vendedor"],))
    v = cursor.fetchone()
    item["vendedor_nombre"] = (v["nombre_usuario"] or v["email"].split("@")[0]) if v else "Vendedor"
    
    cursor.close()
    return item

@router.post("", response_model=ItemResponse)
def crear(datos: ItemCreate, conn = Depends(get_db_connection), user_id: str = Depends(get_current_user)):
    """Añade un producto a la base de datos."""
    item = datos.model_dump()
    item["id_vendedor"] = user_id 
    
    # NOTA PRESENTACIÓN: [META_SQL_INSERT] Mapeo dinámico de llaves del diccionario a columnas y marcadores SQL.
    columnas = ", ".join(item.keys())
    valores = ", ".join(["%s"] * len(item))
    query = f"INSERT INTO articulos ({columnas}) VALUES ({valores})"
    
    try:
        cursor = conn.cursor()
        cursor.execute(query, list(item.values()))
        
        # En MySQL usaríamos cursor.lastrowid.
        # En PostgreSQL (psycopg2) hacemos un SELECT lastval() para obtener el último ID generado.
        cursor.execute("SELECT lastval()")
        last_id = cursor.fetchone()["lastval"]
        
        # Obtenemos la fila recién creada de forma estándar (compatible con MySQL y PostgreSQL)
        cursor.execute("SELECT * FROM articulos WHERE id_articulo = %s", (last_id,))
        nuevo = cursor.fetchone()
        
        # NOTA PRESENTACIÓN: [DB_COMMIT] Confirmación física de los cambios en la base de datos.
        conn.commit()
        cursor.close()
        return {**nuevo, "fotos": []}
    except Exception as e:
        conn.rollback()
        raise HTTPException(500, "Fallo al guardar en la base de datos")

@router.patch("/{id}", response_model=ItemResponse)
async def editar(id: int, datos: ItemUpdate, conn = Depends(get_db_connection), user_id: str = Depends(get_current_user)):
    """Cambia datos de un producto tuyo."""
    await soy_el_dueño(id, user_id, conn)
    
    dict_datos = datos.model_dump(exclude_unset=True)
    if not dict_datos: raise HTTPException(400, "Nada que cambiar")

    sets = ", ".join([f"{c} = %s" for c in dict_datos.keys()])
    query = f"UPDATE articulos SET {sets} WHERE id_articulo = %s"
    params = list(dict_datos.values()) + [id]
    
    try:
        cursor = conn.cursor()
        cursor.execute(query, params)
        
        # Obtenemos la fila actualizada de forma estándar (compatible con MySQL y PostgreSQL)
        cursor.execute("SELECT * FROM articulos WHERE id_articulo = %s", (id,))
        editado = cursor.fetchone()
        
        # Fotos para que no se pierdan en el frontend
        query_fotos = "SELECT * FROM fotos_articulo WHERE id_articulo = %s"
        cursor.execute(query_fotos, (id,))
        editado["fotos"] = cursor.fetchall()
        
        conn.commit()
        cursor.close()
        return editado
    except Exception as e:
        conn.rollback()
        raise HTTPException(500, "Fallo al actualizar")

@router.delete("/{id}")
async def borrar(id: int, conn = Depends(get_db_connection), user_id: str = Depends(get_current_user)):
    """Elimina el producto para siempre."""
    await soy_el_dueño(id, user_id, conn)
    try:
        cursor = conn.cursor()
        query = "DELETE FROM articulos WHERE id_articulo = %s"
        cursor.execute(query, (id,))
        conn.commit()
        cursor.close()
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
        
        cursor = conn.cursor()
        query = "INSERT INTO fotos_articulo (id_articulo, image_url) VALUES (%s, %s)"
        cursor.execute(query, (id, url))
        conn.commit()
        cursor.close()
        
        return {"image_url": url}
    except Exception:
        conn.rollback()
        raise HTTPException(500, "Error con la foto")
