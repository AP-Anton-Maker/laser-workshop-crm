from pydantic import BaseModel, Field, ConfigDict
from datetime import datetime
from typing import Optional, Dict, Any


class OrderBase(BaseModel):
    """Базовая схема заказа с общими полями"""
    service_name: str = Field(..., description="Название услуги (например, 'Гравировка на металле')")
    parameters: Dict[str, Any] = Field(default_factory=dict, description="Параметры реза/гравировки (словарь)")
    total_price: float = Field(..., gt=0, description="Итоговая стоимость заказа")
    discount: float = Field(default=0.0, ge=0, le=100, description="Скидка в процентах или рублях (зависит от логики)")
    cashback_applied: float = Field(default=0.0, ge=0, description="Сумма списанного кэшбэка")
    status: str = Field(default="NEW", description="Статус заказа: NEW, PROCESSING, READY, COMPLETED, CANCELLED")
    planned_date: Optional[datetime] = Field(None, description="Планируемая дата выполнения")


class OrderCreate(OrderBase):
    """Схема для создания нового заказа (данные от фронтенда)"""
    client_id: int = Field(..., description="ID клиента")
    calc_type: str = Field(..., description="Тип калькулятора для проверки цены (fixed, area_cm2...)")
    server_base_price: float = Field(..., description="Базовая ставка, использованная для расчета на клиенте")
    # parameters уже есть в базовом классе как Dict, при сохранении превратим в JSON строку
    
    model_config = ConfigDict(
        json_schema_extra={
            "example": {
                "client_id": 1,
                "service_name": "Резка фанеры",
                "parameters": {"material": "Фанера 4мм", "speed": 20, "power": 80},
                "total_price": 1500.0,
                "discount": 0,
                "cashback_applied": 0,
                "status": "NEW",
                "planned_date": "2023-12-25T10:00:00"
            }
        }
    )


class OrderStatusUpdate(BaseModel):
    """Схема для обновления статуса заказа"""
    order_id: int = Field(..., description="ID заказа")
    status: str = Field(..., description="Новый статус")


class OrderResponse(OrderBase):
    """Схема ответа сервера (с дополнительными полями из БД)"""
    id: int
    client_id: int
    client_name: Optional[str] = None  # Имя клиента для удобства отображения
    created_at: datetime
    updated_at: Optional[datetime] = None

    # Разрешаем преобразование моделей SQLAlchemy в Pydantic объекты
    model_config = ConfigDict(from_attributes=True)
