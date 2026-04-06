from pydantic import BaseModel, ConfigDict, Field
from typing import Optional, List
from datetime import datetime
from db.models import UserRole, OrderStatus, OrderPriority, ChatDirection

# --- Авторизация (Tokens) ---

class Token(BaseModel):
    access_token: str
    token_type: str

class TokenData(BaseModel):
    username: Optional[str] = None

# --- Пользователи (Users) ---

class UserCreate(BaseModel):
    username: str = Field(..., min_length=3, max_length=50)
    password: str = Field(..., min_length=6)
    role: Optional[UserRole] = UserRole.manager

class UserResponse(BaseModel):
    id: int
    username: str
    role: UserRole
    is_active: bool
    
    model_config = ConfigDict(from_attributes=True)

# --- Клиенты (Clients) ---

class ClientCreate(BaseModel):
    name: str = Field(..., min_length=1, max_length=100)
    vk_id: Optional[int] = None
    phone: Optional[str] = None
    notes: Optional[str] = None

class ClientUpdate(BaseModel):
    name: Optional[str] = None
    vk_id: Optional[int] = None
    phone: Optional[str] = None
    notes: Optional[str] = None
    ltv: Optional[float] = None
    cashback_balance: Optional[float] = None

class ClientResponse(BaseModel):
    id: int
    name: str
    vk_id: Optional[int]
    phone: Optional[str]
    ltv: float
    notes: Optional[str]
    cashback_balance: float
    created_at: datetime
    
    model_config = ConfigDict(from_attributes=True)

# --- Заказы (Orders) ---

class OrderCreate(BaseModel):
    client_id: int
    description: str
    price: Optional[float] = 0.0
    cost_price: Optional[float] = 0.0
    deadline: Optional[datetime] = None
    priority: Optional[OrderPriority] = OrderPriority.NORMAL

class OrderUpdate(BaseModel):
    description: Optional[str] = None
    status: Optional[OrderStatus] = None
    price: Optional[float] = None
    cost_price: Optional[float] = None
    deadline: Optional[datetime] = None
    priority: Optional[OrderPriority] = None

class OrderResponse(BaseModel):
    id: int
    client_id: int
    description: str
    status: OrderStatus
    price: float
    cost_price: float
    deadline: Optional[datetime]
    priority: OrderPriority
    created_at: datetime
    
    model_config = ConfigDict(from_attributes=True)

# --- Склад (Inventory) ---

class InventoryCreate(BaseModel):
    name: str
    quantity: Optional[float] = 0.0
    min_quantity_alert: Optional[float] = 10.0

class InventoryUpdate(BaseModel):
    name: Optional[str] = None
    quantity: Optional[float] = None
    min_quantity_alert: Optional[float] = None

class InventoryResponse(BaseModel):
    id: int
    name: str
    quantity: float
    min_quantity_alert: float
    
    model_config = ConfigDict(from_attributes=True)

# --- Чат ВК (Chat Messages) ---

class ChatMessageResponse(BaseModel):
    id: int
    client_id: int
    direction: ChatDirection
    text: str
    is_read: bool
    timestamp: datetime
    
    model_config = ConfigDict(from_attributes=True)
