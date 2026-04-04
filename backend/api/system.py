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
from ..api.auth import get_current_user
from ..db.models import User

router = APIRouter(prefix="/api/system", tags=["System"])


@router.get("/export/orders")
async def export_orders_csv(db: AsyncSession = Depends(get_db), current_user: User = Depends(get_current_user)):
    stmt = select(Order).order_by(Order.created_at.desc())
    result = await db.execute(stmt)
    orders = result.scalars().all()
    
    output = io.StringIO()
    writer = csv.writer(output)
    writer.writerow(["ID", "Клиент", "Услуга", "Цена", "Статус", "Дата создания"])
    
    for order in orders:
        writer.writerow([
            order.id, f"Client_{order.client_id}", order.service_name,
            order.total_price, order.status, order.created_at.strftime("%Y-%m-%d %H:%M")
        ])
    
    output.seek(0)
    return StreamingResponse(output, media_type="text/csv", headers={"Content-Disposition": "attachment; filename=orders.csv"})

@router.get("/export/clients")
async def export_clients_csv(db: AsyncSession = Depends(get_db), current_user: User = Depends(get_current_user)):
    stmt = select(Client).order_by(Client.total_spent.desc())
    result = await db.execute(stmt)
    clients = result.scalars().all()
    
    output = io.StringIO()
    writer = csv.writer(output)
    writer.writerow(["ID", "Имя", "VK_ID", "Сегмент", "Заказов", "LTV", "Кэшбэк"])
    
    for client in clients:
        writer.writerow([
            client.id, client.name, client.vk_id, client.segment,
            client.total_orders, client.total_spent, client.cashback_balance
        ])
    
    output.seek(0)
    return StreamingResponse(output, media_type="text/csv", headers={"Content-Disposition": "attachment; filename=clients.csv"})

@router.get("/backup/download")
async def download_backup(current_user: User = Depends(get_current_user)):
    backup_path = await create_db_backup()
    if not backup_path:
        raise HTTPException(status_code=500, detail="Failed to create backup")
    
    filename = backup_path.split("/")[-1]
    return FileResponse(path=backup_path, media_type="application/octet-stream", filename=filename)

# --- НОВЫЕ ЭНДПОИНТЫ ДЛЯ НАСТРОЕК ОТПУСКА ---

@router.get("/settings")
async def get_system_settings(db: AsyncSession = Depends(get_db), current_user: User = Depends(get_current_user)):
    """
    Получение системных настроек.
    Если запись не найдена, создает дефолтную с id=1.
    """
    stmt = select(SystemSettings).where(SystemSettings.id == 1)
    result = await db.execute(stmt)
    settings = result.scalars().first()

    if not settings:
        # Создаем дефолтные настройки, если их нет
        settings = SystemSettings(
            id=1,
            is_vacation_mode=False,
            vacation_end_date=None,
            vacation_message="Здравствуйте! Я сейчас в отпуске. Отвечу вам, как только вернусь."
        )
        db.add(settings)
        await db.commit()
        await db.refresh(settings)

    return {
        "is_vacation_mode": settings.is_vacation_mode,
        "vacation_end_date": settings.vacation_end_date,
        "vacation_message": settings.vacation_message
    }

@router.post("/settings")
async def update_system_settings(
    settings_ dict,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """
    Обновление системных настроек (включение режима отпуска).
    """
    stmt = select(SystemSettings).where(SystemSettings.id == 1)
    result = await db.execute(stmt)
    settings = result.scalars().first()

    if not settings:
        # Если записи нет, создаем её
        settings = SystemSettings(id=1)
        db.add(settings)

    # Обновляем поля из запроса
    settings.is_vacation_mode = settings_data.get("is_vacation_mode", False)
    settings.vacation_end_date = settings_data.get("vacation_end_date")
    settings.vacation_message = settings_data.get("vacation_message", "Здравствуйте! Я в отпуске.")

    await db.commit()
    await db.refresh(settings)

    return {
        "is_vacation_mode": settings.is_vacation_mode,
        "vacation_end_date": settings.vacation_end_date,
        "vacation_message": settings.vacation_message
    }
