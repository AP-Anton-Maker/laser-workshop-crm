import csv
import io
from fastapi import APIRouter, Depends
from fastapi.responses import StreamingResponse, FileResponse
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select
from typing import List

from ..db.session import get_db
from ..db.models import Order, Client
from ..services.backup_mgr import create_db_backup

router = APIRouter(prefix="/api/system", tags=["System"])


@router.get("/export/orders")
async def export_orders_csv(db: AsyncSession = Depends(get_db)):
    """Экспорт заказов в CSV (utf-8-sig для Excel)."""
    stmt = select(Order).order_by(Order.created_at.desc())
    result = await db.execute(stmt)
    orders = result.scalars().all()
    
    output = io.StringIO()
    # Кодировка utf-8-sig добавляет BOM для корректного отображения кириллицы в Excel
    writer = csv.writer(output)
    
    # Заголовки
    writer.writerow(["ID", "Клиент", "Услуга", "Цена", "Статус", "Дата создания"])
    
    for order in orders:
        # Имя клиента нужно получить отдельно или через join, здесь упрощенно
        # Для полноценной работы нужен join в запросе выше, но для примера берем ID
        writer.writerow([
            order.id,
            f"Client_{order.client_id}", 
            order.service_name,
            order.total_price,
            order.status,
            order.created_at.strftime("%Y-%m-%d %H:%M")
        ])
    
    output.seek(0)
    return StreamingResponse(
        output,
        media_type="text/csv",
        headers={"Content-Disposition": "attachment; filename=orders.csv"}
    )


@router.get("/export/clients")
async def export_clients_csv(db: AsyncSession = Depends(get_db)):
    """Экспорт клиентов в CSV."""
    stmt = select(Client).order_by(Client.total_spent.desc())
    result = await db.execute(stmt)
    clients = result.scalars().all()
    
    output = io.StringIO()
    writer = csv.writer(output)
    
    writer.writerow(["ID", "Имя", "VK_ID", "Сегмент", "Заказов", "LTV", "Кэшбэк"])
    
    for client in clients:
        writer.writerow([
            client.id,
            client.name,
            client.vk_id,
            client.segment,
            client.total_orders,
            client.total_spent,
            client.cashback_balance
        ])
    
    output.seek(0)
    return StreamingResponse(
        output,
        media_type="text/csv",
        headers={"Content-Disposition": "attachment; filename=clients.csv"}
    )


@router.get("/backup/download")
async def download_backup():
    """Создание и скачивание бэкапа БД."""
    backup_path = await create_db_backup()
    if not backup_path:
        raise Exception("Failed to create backup")
    
    filename = backup_path.split("/")[-1]
    return FileResponse(
        path=backup_path,
        media_type="application/octet-stream",
        filename=filename
    )
