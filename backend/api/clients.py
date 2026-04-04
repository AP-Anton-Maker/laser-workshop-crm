from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select
from typing import List

from ..db.session import get_db
from ..db.models import Client, CashbackHistory
from ..schemas.client import ClientResponse, CashbackHistoryResponse

router = APIRouter(prefix="/api", tags=["Clients"])


@router.get("/clients", response_model=List[ClientResponse])
async def get_clients(
    segment: str = Query(None, description="Фильтр по сегменту"),
    db: AsyncSession = Depends(get_db)
):
    """Получение списка клиентов с опциональной фильтрацией по сегменту."""
    stmt = select(Client)
    if segment:
        stmt = stmt.where(Client.segment == segment.lower())
    
    stmt = stmt.order_by(Client.total_spent.desc())
    result = await db.execute(stmt)
    return result.scalars().all()


@router.get("/cashback/history/{client_id}", response_model=List[CashbackHistoryResponse])
async def get_cashback_history(client_id: int, db: AsyncSession = Depends(get_db)):
    """История операций кэшбэка для конкретного клиента."""
    stmt = (
        select(CashbackHistory)
        .where(CashbackHistory.client_id == client_id)
        .order_by(CashbackHistory.created_at.desc())
    )
    result = await db.execute(stmt)
    return result.scalars().all()
