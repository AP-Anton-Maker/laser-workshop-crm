from pydantic import BaseModel, Field, ConfigDict
from datetime import datetime
from typing import Optional, Dict, Any, List


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


class OrderListResponse(BaseModel):
    orders: List[OrderResponse]
    total: int
