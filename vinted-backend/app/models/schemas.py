from pydantic import BaseModel
from typing import Optional
from datetime import datetime

# Shared properties
class ArticuloBase(BaseModel):
    titulo: str
    descripcion: Optional[str] = None
    precio_base: float

# Properties to receive on item creation
# Properties to receive on item creation
class ArticuloCreate(ArticuloBase):
    pass # We just use 'pass' because it already inherits titulo, descripcion, and precio_base from ArticuloBase!

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