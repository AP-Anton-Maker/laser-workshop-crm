import csv
import io
from fastapi import APIRouter, Depends, HTTPException
from fastapi.responses import StreamingResponse, FileResponse
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select
from sqlalchemy.orm import selectinload
from typing import List
from datetime import datetime

from ..db.session import get_db
from ..db.models import Order, Client
from ..services.backup_mgr import create_db_backup

router = APIRouter(prefix="/api/system", tags=["System & Export"])


@router.get("/export/orders")
async def export_orders_to_csv(db: AsyncSession = Depends(get_db)):
    """
    Экспорт всех заказов в CSV формат (UTF-8-SIG для корректного открытия в Excel).
    Колонки: ID, Клиент, Услуга, Цена, Статус, Дата создания.
    """
    # Загружаем заказы вместе с данными клиента
    stmt = (
        select(Order)
        .options(selectinload(Order.client))
        .order_by(Order.created_at.desc())
    )
    result = await db.execute(stmt)
    orders = result.scalars().all()

    # Создаем буфер в памяти для записи CSV
    output = io.StringIO()
    
    # Важно: encoding='utf-8-sig' добавляет BOM, чтобы Excel понимал кириллицу
    # newline='' нужен для корректной работы модуля csv в Python
    writer = csv.writer(output, quoting=csv.QUOTE_MINIMAL)
    
    # Заголовок таблицы
    writer.writerow(["ID", "Клиент", "Услуга", "Цена (руб)", "Статус", "Дата создания"])
    
    for order in orders:
        client_name = order.client.name if order.client else "Неизвестно"
        date_str = order.created_at.strftime("%Y-%m-%d %H:%M") if order.created_at else ""
        
        writer.writerow([
            order.id,
            client_name,
            order.service_name,
            order.total_price,
            order.status,
            date_str
        ])
    
    # Получаем значение из буфера
    csv_content = output.getvalue()
    output.close()
    
    # Создаем StreamingResponse
    response = StreamingResponse(
        iter([csv_content.encode('utf-8-sig')]), 
        media_type="text/csv"
    )
    response.headers["Content-Disposition"] = f"attachment; filename=orders_export_{datetime.now().strftime('%Y%m%d')}.csv"
    
    return response


@router.get("/export/clients")
async def export_clients_to_csv(db: AsyncSession = Depends(get_db)):
    """
    Экспорт всех клиентов в CSV формат.
    Колонки: ID, Имя, VK_ID, Сегмент, Всего заказов, LTV (Всего потрачено), Кэшбек баланс.
    """
    stmt = select(Client).order_by(Client.total_spent.desc())
    result = await db.execute(stmt)
    clients = result.scalars().all()

    output = io.StringIO()
    writer = csv.writer(output, quoting=csv.QUOTE_MINIMAL)
    
    writer.writerow(["ID", "Имя", "VK_ID", "Сегмент", "Всего заказов", "LTV (руб)", "Кэшбек (баллы)"])
    
    for client in clients:
        writer.writerow([
            client.id,
            client.name,
            client.vk_id or "",
            client.segment,
            client.total_orders,
            client.total_spent,
            client.cashback_balance
        ])
    
    csv_content = output.getvalue()
    output.close()
    
    response = StreamingResponse(
        iter([csv_content.encode('utf-8-sig')]), 
        media_type="text/csv"
    )
    response.headers["Content-Disposition"] = f"attachment; filename=clients_export_{datetime.now().strftime('%Y%m%d')}.csv"
    
    return response


@router.get("/backup/download")
async def download_database_backup():
    """
    Создает свежий бэкап базы данных и инициирует его скачивание.
    """
    try:
        backup_file_path = await create_db_backup()
        
        # Извлекаем только имя файла для заголовка Content-Disposition
        file_name = backup_file_path.split("/")[-1]
        
        return FileResponse(
            path=backup_file_path,
            media_type="application/octet-stream",
            filename=file_name,
            headers={
                "Content-Disposition": f"attachment; filename={file_name}"
            }
        )
        
    except FileNotFoundError as e:
        raise HTTPException(status_code=404, detail=str(e))
    except IOError as e:
        raise HTTPException(status_code=500, detail=str(e))
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Непредвиденная ошибка: {str(e)}")
