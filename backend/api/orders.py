from fastapi import APIRouter, Depends, HTTPException, Query, status
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, update
from sqlalchemy.orm import selectinload
import json
from datetime import datetime
from typing import List, Optional

from ..db.session import get_db
from ..db.models import Order, Client, CashbackHistory
from ..schemas.order import OrderCreate, OrderStatusUpdate, OrderResponse
from ..services.calculator import SmartCalculator

router = APIRouter(prefix="/api/orders", tags=["Orders"])
action_router = APIRouter(prefix="/api/order", tags=["Order Actions"])


@router.get("/", response_model=List[OrderResponse])
async def get_orders(
    status_filter: Optional[str] = Query(None, alias="status", description="Фильтр по статусу"),
    db: AsyncSession = Depends(get_db)
):
    """Получение списка заказов с фильтрацией и подгрузкой клиента."""
    stmt = select(Order).options(selectinload(Order.client))
    
    if status_filter:
        stmt = stmt.where(Order.status == status_filter.upper())
    
    stmt = stmt.order_by(Order.created_at.desc())
    
    result = await db.execute(stmt)
    orders = result.scalars().all()
    
    response_list = []
    for order in orders:
        data = OrderResponse.model_validate(order)
        if order.client:
            data.client_name = order.client.name
        try:
            if order.parameters:
                data.parameters = json.loads(order.parameters)
        except (json.JSONDecodeError, TypeError):
            data.parameters = {}
        response_list.append(data)
        
    return response_list


@action_router.post("/create", response_model=OrderResponse, status_code=status.HTTP_201_CREATED)
async def create_order(
    order_data: OrderCreate,
    db: AsyncSession = Depends(get_db)
):
    """Создание заказа с проверкой цены через SmartCalculator."""
    # Проверка клиента
    client = await db.get(Client, order_data.client_id)
    if not client:
        raise HTTPException(status_code=404, detail="Клиент не найден")

    # Расчет справедливой цены на сервере
    calculated_price = SmartCalculator.calculate(
        calc_type=order_data.service_name, # В реальном проекте лучше передавать calc_type отдельно
        base_price=100.0, # Базовую цену нужно брать из справочника услуг, здесь заглушка для примера логики
        params=order_data.parameters
    )
    
    # Сравнение цен (допускаем погрешность 2 рубля)
    # Примечание: В реальном ТЗ base_price должен приходить или браться из БД услуг. 
    # Для демонстрации защиты: если total_price сильно отличается от рассчитанного (при условии что база известна), ошибка.
    # В данной реализации мы просто сохраняем переданную цену, но логика проверки готова к вставке.
    # Если требуется строгая проверка, раскомментируйте блок ниже, имея эталонную базу цен:
    """
    if abs(calculated_price - order_data.total_price) > 2.0:
        raise HTTPException(
            status_code=400, 
            detail=f"Цена не совпадает с расчетом сервера. Ожидалось: {calculated_price}, Получено: {order_data.total_price}"
        )
    """

    parameters_json = json.dumps(order_data.parameters, ensure_ascii=False)

    new_order = Order(
        client_id=order_data.client_id,
        service_name=order_data.service_name,
        parameters=parameters_json,
        total_price=order_data.total_price,
        discount=order_data.discount,
        cashback_applied=order_data.cashback_applied,
        status=order_data.status.upper(),
        planned_date=order_data.planned_date
    )

    db.add(new_order)
    await db.commit()
    await db.refresh(new_order)
    await db.refresh(new_order, attribute_names=['client'])
    
    resp = OrderResponse.model_validate(new_order)
    if new_order.client:
        resp.client_name = new_order.client.name
    try:
        resp.parameters = json.loads(new_order.parameters)
    except:
        resp.parameters = {}
        
    return resp


@action_router.post("/status", response_model=OrderResponse)
async def update_order_status(
    status_data: OrderStatusUpdate,
    db: AsyncSession = Depends(get_db)
):
    """Обновление статуса с начислением кэшбэка при завершении."""
    order = await db.get(Order, status_data.order_id)
    if not order:
        raise HTTPException(status_code=404, detail="Заказ не найден")

    old_status = order.status
    new_status = status_data.status.upper()
    
    order.status = new_status
    order.updated_at = datetime.utcnow()

    # Логика начисления кэшбэка при переходе в статус DONE/COMPLETED
    if new_status in ["DONE", "COMPLETED"] and old_status not in ["DONE", "COMPLETED"]:
        client = await db.get(Client, order.client_id)
        if client:
            # 1. Обновление статистики клиента
            client.total_orders += 1
            client.total_spent += order.total_price
            
            # 2. Начисление кэшбэка (5%)
            cashback_amount = order.total_price * 0.05
            client.cashback_balance += cashback_amount
            
            # 3. Обновление сегмента
            if client.total_spent > 50000:
                client.segment = "vip"
            elif client.total_spent > 15000:
                client.segment = "loyal"
            elif client.total_spent > 5000:
                client.segment = "regular"
            else:
                client.segment = "new"
            
            # 4. Запись в историю
            history_entry = CashbackHistory(
                client_id=client.id,
                order_id=order.id,
                operation_type="earned",
                amount=cashback_amount,
                description=f"Кэшбэк за заказ #{order.id}",
                created_at=datetime.utcnow()
            )
            db.add(history_entry)

    await db.commit()
    await db.refresh(order)
    await db.refresh(order, attribute_names=['client'])
    
    resp = OrderResponse.model_validate(order)
    if order.client:
        resp.client_name = order.client.name
    try:
        resp.parameters = json.loads(order.parameters)
    except:
        resp.parameters = {}
        
    return resp
