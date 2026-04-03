from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, update
from sqlalchemy.orm import selectinload
import json
from datetime import datetime
from typing import List, Optional

# Импорты моделей и схем
from ..db.session import get_db
from ..db.models import Order, Client
from ..schemas.order import OrderCreate, OrderStatusUpdate, OrderResponse
from ..services.calculator import SmartCalculator

# Создаем роутеры
router = APIRouter(prefix="/api/orders", tags=["Orders"])
action_router = APIRouter(prefix="/api/order", tags=["Order Actions"])


@router.get("/", response_model=List[OrderResponse])
async def get_orders(
    status: Optional[str] = Query(None, description="Фильтр по статусу (NEW, PROCESSING и т.д.)"),
    db: AsyncSession = Depends(get_db)
):
    """
    Получение списка всех заказов.
    Опционально можно фильтровать по статусу через query параметр ?status=NEW
    """
    # Формируем базовый запрос с подгрузкой связанного клиента (чтобы получить имя)
    stmt = select(Order).options(selectinload(Order.client))
    
    if status:
        # Приводим статус к верхнему регистру для единообразия, если нужно
        stmt = stmt.where(Order.status == status.upper())
    
    # Добавляем сортировку по дате создания (новые сверху)
    stmt = stmt.order_by(Order.created_at.desc())
    
    result = await db.execute(stmt)
    orders = result.scalars().all()
    
    # Формируем ответ, добавляя имя клиента вручную, так как в модели ответа оно отдельным полем
    response_list = []
    for order in orders:
        # Конвертируем параметры из JSON строки обратно в словарь для ответа
        order_data = OrderResponse.model_validate(order)
        if order.client:
            order_data.client_name = order.client.name
        # Преобразуем строку параметров обратно в dict для фронтенда
        try:
            if order.parameters:
                order_data.parameters = json.loads(order.parameters)
        except (json.JSONDecodeError, TypeError):
            order_data.parameters = {}
            
        response_list.append(order_data)
        
    return response_list


@action_router.post("/create", response_model=OrderResponse, status_code=201)
async def create_order(
    order_data: OrderCreate,
    db: AsyncSession = Depends(get_db)
):
    """
    Создание нового заказа с серверной проверкой цены.
    """
    # 1. Проверка существования клиента
    client_check = await db.get(Client, order_data.client_id)
    if not client_check:
        raise HTTPException(status_code=404, detail="Клиент не найден")

    # 2. СЕРВЕРНЫЙ РАСЧЕТ ЦЕНЫ
    try:
        calculated_price = SmartCalculator.calculate(
            calc_type=order_data.calc_type,
            base_price=order_data.server_base_price,
            params=order_data.parameters
        )
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Ошибка калькулятора: {str(e)}")

    # 3. СРАВНЕНИЕ ЦЕН
    # Допускаем погрешность в 2 рубля из-за различий округления на клиенте/сервере
    if abs(calculated_price - order_data.total_price) > 2.0:
        raise HTTPException(
            status_code=400, 
            detail=f"Несоответствие цены! Клиент прислал: {order_data.total_price}, "
                   f"Сервер рассчитал: {calculated_price}. Пожалуйста, обновите страницу."
        )

    # 4. Сериализация параметров и сохранение
    parameters_json = json.dumps(order_data.parameters, ensure_ascii=False)

    new_order = Order(
        client_id=order_data.client_id,
        service_name=order_data.service_name,
        parameters=parameters_json,
        total_price=calculated_price, # Сохраняем ТОЛЬКО серверную цену!
        discount=order_data.discount,
        cashback_applied=order_data.cashback_applied,
        status=order_data.status.upper(),
        planned_date=order_data.planned_date
    )

    db.add(new_order)
    await db.commit()
    await db.refresh(new_order)
    
    # Подготовка ответа
    await db.refresh(new_order, attribute_names=['client'])
    
    response_data = OrderResponse.model_validate(new_order)
    if new_order.client:
        response_data.client_name = new_order.client.name
    
    try:
        response_data.parameters = json.loads(new_order.parameters)
    except:
        response_data.parameters = {}
        
    return response_data
