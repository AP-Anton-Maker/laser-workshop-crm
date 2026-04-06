from typing import List
from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.future import select

from db.session import get_db
from db.models import Order, Client, User, OrderStatus
from schemas import OrderCreate, OrderUpdate, OrderResponse
from api.deps import get_current_active_user

router = APIRouter(prefix="/orders", tags=["Заказы"])

@router.post("/", response_model=OrderResponse, status_code=status.HTTP_201_CREATED)
async def create_order(
    order_in: OrderCreate,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_active_user)
):
    """Создает новый заказ и привязывает его к клиенту."""
    client = await db.get(Client, order_in.client_id)
    if not client:
        raise HTTPException(status_code=404, detail="Указанный клиент не найден")

    new_order = Order(**order_in.model_dump())
    db.add(new_order)
    await db.commit()
    await db.refresh(new_order)
    return new_order

@router.get("/", response_model=List[OrderResponse])
async def read_orders(
    skip: int = 0,
    limit: int = 100,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_active_user)
):
    """Возвращает список всех заказов."""
    stmt = select(Order).offset(skip).limit(limit).order_by(Order.id.desc())
    result = await db.execute(stmt)
    return result.scalars().all()

@router.put("/{order_id}", response_model=OrderResponse)
async def update_order(
    order_id: int,
    order_in: OrderUpdate,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_active_user)
):
    """Стандартное обновление данных заказа."""
    order = await db.get(Order, order_id)
    if not order:
        raise HTTPException(status_code=404, detail="Заказ не найден")

    update_data = order_in.model_dump(exclude_unset=True)
    for field, value in update_data.items():
        setattr(order, field, value)

    await db.commit()
    await db.refresh(order)
    return order

@router.post("/{order_id}/action/status", response_model=OrderResponse)
async def change_order_status(
    order_id: int,
    new_status: OrderStatus,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_active_user)
):
    """
    Специальный эндпоинт для бизнес-процесса: Изменение статуса заказа.
    СИСТЕМА ЛОЯЛЬНОСТИ: Если статус меняется на DELIVERED, начисляется кэшбэк.
    """
    order = await db.get(Order, order_id)
    if not order:
        raise HTTPException(status_code=404, detail="Заказ не найден")

    # Проверка: если заказ УЖЕ был выдан, не начисляем кэшбэк повторно
    if new_status == OrderStatus.DELIVERED and order.status != OrderStatus.DELIVERED:
        client = await db.get(Client, order.client_id)
        if client:
            # Расчет 5% кэшбэка от цены заказа
            cashback_amount = round(order.price * 0.05, 2)
            
            client.cashback_balance += cashback_amount
            client.ltv += order.price
            
            # Добавляем лог в заметки клиента
            note_addition = f"\n[Лояльность]: +{cashback_amount} руб. кэшбэк за заказ #{order.id}"
            client.notes = (client.notes + note_addition) if client.notes else note_addition

    order.status = new_status
    await db.commit()
    await db.refresh(order)
    return order

@router.delete("/{order_id}", status_code=status.HTTP_204_NO_CONTENT)
async def delete_order(
    order_id: int,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_active_user)
):
    """Удаляет заказ из системы."""
    order = await db.get(Order, order_id)
    if not order:
        raise HTTPException(status_code=404, detail="Заказ не найден")
        
    await db.delete(order)
    await db.commit()
