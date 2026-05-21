from pydantic import BaseModel
from typing import Optional, List
from datetime import datetime
from enum import Enum

# --- Enums (Categories and States) ---

class ItemStatus(str, Enum):
    """
    Defines the possible states of an item. 
    Using an Enum prevents typos and makes the code more robust.
    """
    available = "disponible"
    reserved = "reservado"
    sold = "vendido"
    deactivated = "desactivado"
    deleted = "eliminado"

# --- Item Schemas ---

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
    id_vendedor: str # UUID from Auth
    estado_articulo: ItemStatus
    fotos: Optional[List[PhotoResponse]] = []
    created_at: Optional[datetime] = None
    updated_at: Optional[datetime] = None

# --- Auth / User Schemas ---

class UserCreate(BaseModel):
    email: str
    password: str

class UserResponse(BaseModel):
    id_usuario: str # UUID
    email: str
    estado: Optional[str] = "activo"
    rol: Optional[str] = "user"
    created_at: Optional[datetime] = None

class TokenResponse(BaseModel):
    access_token: str
    token_type: str = "bearer"

# --- Offer Schemas ---

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
    created_at: Optional[datetime] = None
    updated_at: Optional[datetime] = None

# --- Message Schemas ---

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

# --- Favorite / Order Schemas ---

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
