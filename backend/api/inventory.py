from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select
from typing import List

from ..db.session import get_db
from ..db.models import Inventory
from ..schemas.inventory import InventoryCreate, InventoryUpdate, InventoryResponse

router = APIRouter(prefix="/api/inventory", tags=["Inventory"])


@router.get("/", response_model=List[InventoryResponse])
async def get_all_inventory(db: AsyncSession = Depends(get_db)):
    """Полный список товаров на складе."""
    stmt = select(Inventory).order_by(Inventory.item_name.asc())
    result = await db.execute(stmt)
    return result.scalars().all()


@router.get("/low-stock", response_model=List[InventoryResponse])
async def get_low_stock_items(db: AsyncSession = Depends(get_db)):
    """Товары, требующие пополнения (quantity <= min_quantity)."""
    stmt = select(Inventory).where(Inventory.quantity <= Inventory.min_quantity)
    result = await db.execute(stmt)
    return result.scalars().all()


@router.post("/create", response_model=InventoryResponse, status_code=status.HTTP_201_CREATED)
async def create_inventory_item(item_data: InventoryCreate, db: AsyncSession = Depends(get_db)):
    """Добавление новой позиции на склад."""
    new_item = Inventory(**item_data.model_dump())
    db.add(new_item)
    await db.commit()
    await db.refresh(new_item)
    return new_item


@router.post("/update", response_model=InventoryResponse)
async def update_inventory_item(item_data: InventoryUpdate, db: AsyncSession = Depends(get_db)):
    """Обновление параметров существующей позиции."""
    item = await db.get(Inventory, item_data.id)
    if not item:
        raise HTTPException(status_code=404, detail="Позиция не найдена")

    update_data = item_data.model_dump(exclude_unset=True, exclude={'id'})
    for field, value in update_data.items():
        if value is not None:
            setattr(item, field, value)
            
    await db.commit()
    await db.refresh(item)
    return item
