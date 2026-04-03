from pydantic import BaseModel, Field, ConfigDict
from typing import Optional
from datetime import datetime


class InventoryBase(BaseModel):
    """Базовая схема для складских позиций"""
    item_name: str = Field(..., description="Название товара/материала")
    item_type: str = Field(..., description="Тип (материал, инструмент, расходник)")
    quantity: float = Field(..., ge=0, description="Текущее количество")
    min_quantity: float = Field(..., ge=0, description="Минимальный порог для уведомления")
    unit: str = Field(default="шт", description="Единица измерения (шт, м, кг, лист)")
    price_per_unit: float = Field(..., ge=0, description="Цена за единицу")
    supplier: Optional[str] = Field(None, description="Поставщик")
    notes: Optional[str] = Field(None, description="Примечания")


class InventoryCreate(InventoryBase):
    """Схема для создания новой позиции на складе"""
    # Все поля обязательны при создании, кроме notes и supplier
    pass


class InventoryUpdate(BaseModel):
    """Схема для обновления существующей позиции"""
    id: int = Field(..., description="ID позиции на складе")
    quantity: Optional[float] = Field(None, ge=0, description="Новое количество")
    min_quantity: Optional[float] = Field(None, ge=0, description="Новый минимальный порог")
    price_per_unit: Optional[float] = Field(None, ge=0, description="Новая цена")
    supplier: Optional[str] = Field(None, description="Новый поставщик")
    notes: Optional[str] = Field(None, description="Новые примечания")
    # item_name и item_type обычно не меняются, но можно добавить при необходимости


class InventoryResponse(InventoryBase):
    """Схема ответа сервера"""
    id: int
    created_at: datetime
    updated_at: Optional[datetime] = None

    model_config = ConfigDict(from_attributes=True)
