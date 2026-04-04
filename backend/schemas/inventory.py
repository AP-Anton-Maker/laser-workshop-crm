from pydantic import BaseModel, Field, ConfigDict
from datetime import datetime
from typing import Optional


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
