from pydantic import BaseModel, Field, ConfigDict
from datetime import datetime
from typing import Optional, Dict, Any, List

# --- Token / Auth ---
class Token(BaseModel):
    access_token: str
    token_type: str = "bearer"

class TokenData(BaseModel):
    username: Optional[str] = None

# --- Order ---
class OrderBase(BaseModel):
    service_name: str = Field(..., description="Название услуги")
    parameters: Dict[str, Any] = Field(default_factory=dict, description="Параметры заказа")
    total_price: float = Field(..., gt=0, description="Итоговая стоимость")
    discount: float = Field(default=0.0, ge=0, description="Скидка")
    cashback_applied: float = Field(default=0.0, ge=0, description="Примененный кэшбэк")
    status: str = Field(default="NEW", description="Статус заказа")
    planned_date: Optional[datetime] = Field(None, description="Планируемая дата")

class OrderCreate(OrderBase):
    client_id: int = Field(..., description="ID клиента")

class OrderStatusUpdate(BaseModel):
    order_id: int = Field(..., description="ID заказа")
    status: str = Field(..., description="Новый статус")

class OrderResponse(OrderBase):
    id: int
    client_id: int
    client_name: Optional[str] = None
    created_at: datetime
    updated_at: Optional[datetime] = None

    model_config = ConfigDict(from_attributes=True)

# --- Client ---
class ClientBase(BaseModel):
    name: str = Field(..., description="Имя клиента")
    vk_id: Optional[str] = Field(None, description="ID ВКонтакте")
    phone: Optional[str] = Field(None, description="Телефон")

class ClientCreate(ClientBase):
    pass

class ClientResponse(ClientBase):
    id: int
    segment: str
    total_orders: int
    total_spent: float
    cashback_balance: float
    created_at: datetime

    model_config = ConfigDict(from_attributes=True)

class CashbackHistoryResponse(BaseModel):
    id: int
    client_id: int
    operation_type: str
    amount: float
    description: Optional[str] = None
    created_at: datetime

    model_config = ConfigDict(from_attributes=True)

# --- Inventory ---
class InventoryBase(BaseModel):
    item_name: str = Field(..., description="Название товара")
    item_type: str = Field(..., description="Тип товара")
    quantity: float = Field(..., ge=0, description="Количество")
    min_quantity: float = Field(..., ge=0, description="Минимальный порог")
    unit: str = Field(default="шт", description="Единица измерения")
    price_per_unit: float = Field(..., ge=0, description="Цена за единицу")
    supplier: Optional[str] = Field(None, description="Поставщик")
    notes: Optional[str] = Field(None, description="Примечания")

class InventoryCreate(InventoryBase):
    pass

class InventoryUpdate(BaseModel):
    id: int = Field(..., description="ID позиции")
    quantity: Optional[float] = Field(None, ge=0)
    min_quantity: Optional[float] = Field(None, ge=0)
    price_per_unit: Optional[float] = Field(None, ge=0)
    supplier: Optional[str] = None
    notes: Optional[str] = None

class InventoryResponse(InventoryBase):
    id: int
    created_at: datetime
    updated_at: Optional[datetime] = None

    model_config = ConfigDict(from_attributes=True)

# --- Chat ---
class MessageSend(BaseModel):
    vk_id: int = Field(..., description="ID получателя ВКонтакте")
    message: str = Field(..., min_length=1, description="Текст сообщения")

class ChatHistoryResponse(BaseModel):
    id: int
    vk_id: int
    is_admin: bool
    message_text: str
    timestamp: datetime

    model_config = ConfigDict(from_attributes=True)

# --- System Settings ---
class SystemSettingsResponse(BaseModel):
    is_vacation_mode: bool
    vacation_end_date: Optional[str] = None
    vacation_message: Optional[str] = None

class SystemSettingsUpdate(BaseModel):
    is_vacation_mode: bool = False
    vacation_end_date: Optional[str] = None
    vacation_message: Optional[str] = "Здравствуйте! Я в отпуске."
