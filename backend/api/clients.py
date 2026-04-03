from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select
from typing import List, Optional

from ..db.session import get_db
from ..db.models import Client, CashbackHistory
from ..schemas.client import ClientResponse, CashbackHistoryResponse

router = APIRouter(prefix="/api", tags=["Clients"])


@router.get("/clients", response_model=List[ClientResponse])
async def get_clients(
    segment: Optional[str] = Query(None, description="Фильтр по сегменту (new, regular, loyal, vip)"),
    db: AsyncSession = Depends(get_db)
):
    """
    Получение списка клиентов.
    Опциональная фильтрация по сегменту.
    """
    stmt = select(Client).order_by(Client.total_spent.desc())
    
    if segment:
        stmt = stmt.where(Client.customer_segment == segment.lower())
        
    result = await db.execute(stmt)
    clients = result.scalars().all()
    
    # Формируем ответ с вычислением среднего чека
    response_list = []
    for client in clients:
        client_dict = ClientResponse.model_validate(client)
        client_dict.avg_check = ClientResponse.calculate_avg_check(client.total_spent, client.total_orders)
        response_list.append(client_dict)
        
    return response_list


@router.get("/cashback/history/{client_id}", response_model=List[CashbackHistoryResponse])
async def get_cashback_history(
    client_id: int,
    db: AsyncSession = Depends(get_db)
):
    """
    Получение истории начислений и списаний кэшбэка для конкретного клиента.
    Сортировка: от новых к старым.
    """
    # Проверка существования клиента
    client = await db.get(Client, client_id)
    if not client:
        raise HTTPException(status_code=404, detail="Клиент не найден")

    stmt = (
        select(CashbackHistory)
        .where(CashbackHistory.client_id == client_id)
        .order_by(CashbackHistory.created_at.desc())
    )
    
    result = await db.execute(stmt)
    history = result.scalars().all()
    
    return history
