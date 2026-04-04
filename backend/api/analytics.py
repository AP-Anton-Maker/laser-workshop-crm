from fastapi import APIRouter, Depends, Query
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, func
from sqlalchemy.orm import selectinload
from typing import List, Dict, Any
from datetime import datetime
from calendar import monthrange

from ..db.session import get_db
from ..db.models import Order, Client
from ..services.ai_forecast import predict_revenue

router = APIRouter(prefix="/api", tags=["Analytics"])


@router.get("/analytics/summary")
async def get_dashboard_summary(db: AsyncSession = Depends(get_db)):
    """Сводная статистика для дашборда."""
    stmt_stats = select(
        func.sum(Order.total_price).label("total_revenue"),
        func.count(Order.id).label("total_orders")
    ).where(Order.status.in_(["DONE", "COMPLETED"]))
    
    result = await db.execute(stmt_stats)
    row = result.first()
    
    total_revenue = row.total_revenue or 0.0
    total_orders = row.total_orders or 0
    avg_check = (total_revenue / total_orders) if total_orders > 0 else 0.0

    stmt_cashback = select(func.sum(Client.cashback_balance)).where(Client.cashback_balance > 0)
    res_cb = await db.execute(stmt_cashback)
    total_cashback_outstanding = res_cb.scalar() or 0.0

    stmt_top = select(Client.name, Client.total_spent).order_by(Client.total_spent.desc()).limit(5)
    res_top = await db.execute(stmt_top)
    top_clients = [{"name": r.name, "total_spent": r.total_spent} for r in res_top.all()]

    return {
        "total_revenue": round(total_revenue, 2),
        "total_orders": total_orders,
        "avg_check": round(avg_check, 2),
        "total_cashback_outstanding": round(total_cashback_outstanding, 2),
        "top_clients": top_clients
    }


@router.get("/analytics/services")
async def get_services_revenue(db: AsyncSession = Depends(get_db)):
    """Выручка по услугам."""
    stmt = (
        select(Order.service_name, func.sum(Order.total_price).label("revenue"))
        .where(Order.status.in_(["DONE", "COMPLETED"]))
        .group_by(Order.service_name)
        .order_by(func.sum(Order.total_price).desc())
    )
    result = await db.execute(stmt)
    return [{"service_name": r.service_name, "revenue": r.revenue} for r in result.all()]


@router.get("/analytics/segments")
async def get_clients_segments(db: AsyncSession = Depends(get_db)):
    """Распределение клиентов по сегментам."""
    stmt = select(Client.segment, func.count(Client.id).label("count")).group_by(Client.segment)
    result = await db.execute(stmt)
    return [{"customer_segment": r.segment, "count": r.count} for r in result.all()]


@router.get("/calendar")
async def get_calendar_data(
    month: int = Query(..., ge=1, le=12),
    year: int = Query(..., ge=2020),
    db: AsyncSession = Depends(get_db)
):
    """Заказы по дням месяца для календаря."""
    start_date = datetime(year, month, 1)
    last_day = monthrange(year, month)[1]
    end_date = datetime(year, month, last_day, 23, 59, 59)

    stmt = (
        select(Order)
        .options(selectinload(Order.client))
        .where(Order.planned_date >= start_date)
        .where(Order.planned_date <= end_date)
        .order_by(Order.planned_date.asc())
    )
    
    result = await db.execute(stmt)
    orders = result.scalars().all()
    
    calendar_data: Dict[str, List[Any]] = {}
    
    for order in orders:
        if not order.planned_date:
            continue
        date_key = order.planned_date.strftime("%Y-%m-%d")
        if date_key not in calendar_data:
            calendar_data[date_key] = []
            
        calendar_data[date_key].append({
            "id": order.id,
            "client_name": order.client.name if order.client else "Аноним",
            "service_name": order.service_name,
            "total_price": order.total_price,
            "status": order.status
        })
        
    return calendar_data


@router.get("/ai/predictions")
async def get_ai_predictions(db: AsyncSession = Depends(get_db)):
    """AI-прогноз выручки."""
    prediction_data = await predict_revenue(db)
    if prediction_data is None:
        return {"prediction": 0.0, "trend": "unknown", "confidence": 0.0, "message": "Недостаточно данных"}
    return prediction_data
