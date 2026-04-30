from pydantic import BaseModel
from typing import Optional, List
from datetime import datetime
from enum import Enum

# --- Enums ---
class EstadoArticulo(str, Enum):
    disponible = "disponible"
    reservado = "reservado"
    vendido = "vendido"
    desactivado = "desactivado" # Antes 'eliminado'
    eliminado = "eliminado"      # Antes 'error'

# --- Artículos Schemas ---
class ArticuloBase(BaseModel):
    titulo: str
    descripcion: Optional[str] = None
    precio_base: float
    categoria: str

class ArticuloCreate(ArticuloBase):
    estado_articulo: EstadoArticulo = EstadoArticulo.disponible

class ArticuloUpdate(BaseModel):
    titulo: Optional[str] = None
    descripcion: Optional[str] = None
    precio_base: Optional[float] = None
    categoria: Optional[str] = None
    estado_articulo: Optional[EstadoArticulo] = None

class FotoResponse(BaseModel):
    id_foto: int
    image_url: str
    created_at: datetime

class ArticuloResponse(ArticuloBase):
    id_articulo: int
    id_vendedor: str # UUID
    estado_articulo: EstadoArticulo
    fotos: List[FotoResponse] = []
    created_at: datetime
    updated_at: datetime

# --- Auth / User Schemas ---
class UsuarioCreate(BaseModel):
    email: str
    password: str

class UsuarioResponse(BaseModel):
    id_usuario: str # UUID
    email: str
    estado: str
    created_at: datetime

class TokenResponse(BaseModel):
    access_token: str
    token_type: str = "bearer"

# --- Ofertas Schemas ---
class OfertaCreate(BaseModel):
    id_articulo: int
    importe: float
    mensaje: Optional[str] = None

class OfertaContra(BaseModel):
    nuevo_importe: float
    mensaje: Optional[str] = None

class OfertaResponse(BaseModel):
    id_oferta: int
    estado: str
    importe: float
    mensaje: Optional[str] = None
    id_comprador: str # UUID
    id_articulo: int
    created_at: datetime
    updated_at: datetime

# --- Mensajería Schemas ---
class ConversacionResponse(BaseModel):
    id_conversacion: int
    id_usuario_1: str
    id_usuario_2: str
    id_articulo: int
    created_at: datetime

class MensajeCreate(BaseModel):
    id_destinatario: str
    id_articulo: int
    contenido: str

class MensajeResponse(BaseModel):
    id_mensaje: int
    id_conversacion: int
    id_emisor: str
    contenido: str
    leido: bool
    created_at: datetime

# --- Favoritos Schemas ---
class FavoritoResponse(BaseModel):
    id_favorito: int
    id_usuario: str
    id_articulo: int
    created_at: datetime

# --- Pedidos Schemas ---
class PedidoResponse(BaseModel):
    id_pedido: int
    id_comprador: str
    id_articulo: int
    estado_pedido: str
    precio_final: float
    created_at: datetime
