from pydantic import BaseModel
from typing import Optional, List
from datetime import datetime
from enum import Enum

# --- Enums (Los estados que pueden tener los trastos) ---

class ItemStatus(str, Enum):
    """
    Aquí definimos los estados de un producto. 
    Usamos un Enum para no equivocarnos al escribir y que el código no pete.
    """
    available = "disponible"
    reserved = "reservado"
    sold = "vendido"
    deactivated = "desactivado"
    deleted = "eliminado"

# --- Esquemas de los Artículos ---

class ItemBase(BaseModel):
    titulo: str
    descripcion: Optional[str] = None
    precio_base: float
    categoria: str

class ItemCreate(ItemBase):
    estado_articulo: ItemStatus = ItemStatus.available

class ItemUpdate(BaseModel):
    titulo: Optional[str] = None
    descripcion: Optional[str] = None
    precio_base: Optional[float] = None
    categoria: Optional[str] = None
    estado_articulo: Optional[ItemStatus] = None

class PhotoResponse(BaseModel):
    id_foto: Optional[int] = None
    image_url: str
    created_at: Optional[datetime] = None

class ItemResponse(ItemBase):
    id_articulo: int
    id_vendedor: str # El ID raro que nos da Supabase
    vendedor_nombre: Optional[str] = None
    estado_articulo: ItemStatus
    fotos: Optional[List[PhotoResponse]] = []
    created_at: Optional[datetime] = None
    updated_at: Optional[datetime] = None

# --- Esquemas de Usuarios y Auth ---

class UserCreate(BaseModel):
    email: str
    password: str
    nombre_usuario: Optional[str] = None

class UserResponse(BaseModel):
    id_usuario: str # El UUID (ID largo y raro)
    email: str
    nombre_usuario: Optional[str] = None
    estado: Optional[str] = "activo"
    rol: Optional[str] = "user"
    created_at: Optional[datetime] = None

class TokenResponse(BaseModel):
    access_token: str
    token_type: str = "bearer"

# --- Esquemas de Ofertas ---

class OfferCreate(BaseModel):
    id_articulo: int
    importe: float
    mensaje: Optional[str] = None

class CounterOfferRequest(BaseModel):
    nuevo_importe: float
    mensaje: Optional[str] = None

class OfferResponse(BaseModel):
    id_oferta: int
    estado: str
    importe: float
    mensaje: Optional[str] = None
    id_comprador: str
    id_articulo: int
    articulo_titulo: Optional[str] = None
    created_at: Optional[datetime] = None
    updated_at: Optional[datetime] = None

# --- Esquemas de Mensajes ---

class ConversationResponse(BaseModel):
    id_conversacion: int
    id_usuario_1: str
    id_usuario_2: str
    id_articulo: int
    created_at: Optional[datetime] = None

class MessageCreate(BaseModel):
    id_destinatario: str
    id_articulo: int
    contenido: str

class MessageResponse(BaseModel):
    id_mensaje: int
    id_conversacion: int
    id_emisor: str
    contenido: str
    leido: bool
    created_at: Optional[datetime] = None

# --- Esquemas de Favoritos y Pedidos ---

class FavoriteResponse(BaseModel):
    id_favorito: int
    id_usuario: str
    id_articulo: int
    created_at: Optional[datetime] = None

class OrderResponse(BaseModel):
    id_pedido: int
    id_comprador: str
    id_articulo: int
    estado_pedido: str
    precio_final: float
    created_at: Optional[datetime] = None
    articulo: Optional[ItemResponse] = None
