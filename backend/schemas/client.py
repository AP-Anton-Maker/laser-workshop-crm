from pydantic import BaseModel, Field, ConfigDict
from datetime import datetime
from typing import Optional, List


class ClientBase(BaseModel):
    """Базовая схема клиента"""
    name: str = Field(..., description="Имя клиента")
    vk_id: Optional[str] = Field(None, description="ID ВКонтакте")
    phone: Optional[str] = Field(None, description="Телефон")


class ClientCreate(ClientBase):
    """Схема создания клиента"""
    pass


class ClientResponse(ClientBase):
    """Схема ответа с вычисляемыми полями"""
    id: int
    customer_segment: str
    total_orders: int
    total_spent: float
    cashback_balance: float
    avg_check: float = Field(0.0, description="Средний чек")
    created_at: datetime

    model_config = ConfigDict(from_attributes=True)

    @staticmethod
    def calculate_avg_check(total_spent: float, total_orders: int) -> float:
        if total_orders == 0:
            return 0.0
        return round(total_spent / total_orders, 2)


class CashbackHistoryResponse(BaseModel):
    """Схема истории кэшбэка"""
    id: int
    client_id: int
    order_id: Optional[int] = None
    operation_type: str  # earned, spent
    amount: float
    description: Optional[str] = None
    created_at: datetime

    model_config = ConfigDict(from_attributes=True)
