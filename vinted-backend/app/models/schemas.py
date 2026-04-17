from pydantic import BaseModel
from typing import Optional
from datetime import datetime
from enum import Enum # <-- Añadir esta importación

# --- Enums para mapear la BD ---
class EstadoArticulo(str, Enum):
    disponible = "disponible"
    reservado = "reservado"
    vendido = "vendido"
    oculto = "oculto"

# --- Artículos Schemas ---
class ArticuloBase(BaseModel):
    titulo: str
    descripcion: Optional[str] = None
    precio_base: float

class ArticuloCreate(ArticuloBase):
    pass 

class ArticuloResponse(ArticuloBase):
    id_articulo: str
    id_vendedor: str
    estado_articulo: EstadoArticulo # <-- Usamos el Enum aquí
    created_at: datetime
    updated_at: datetime

# (El resto de esquemas de Auth y Ofertas se quedan igual)

# Properties to return to the frontend
class ArticuloResponse(ArticuloBase):
    id_articulo: str
    estado_articulo: str
    created_at: datetime
    updated_at: datetime

# Add these to your schemas.py
class UsuarioCreate(BaseModel):
    email: str
    password: str

class TokenResponse(BaseModel):
    access_token: str
    token_type: str = "bearer"

class OfertaCreate(BaseModel):
    id_articulo: str
    importe: float
    mensaje: Optional[str] = None # <-- Optional message field

class OfertaContra(BaseModel):
    nuevo_importe: float
    mensaje: Optional[str] = None # <-- Optional message field

class OfertaResponse(BaseModel):
    id_oferta: str
    estado: str
    importe: float
    mensaje: Optional[str] = None # <-- Include in the response
    id_comprador: str
    id_articulo: str
    created_at: datetime
    updated_at: datetime