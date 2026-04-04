import csv
import io
from fastapi import APIRouter, Depends, HTTPException
from fastapi.responses import StreamingResponse, FileResponse
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select
from typing import List, Dict

from ..db.session import get_db
from ..db.models import Order, Client, SystemSettings, User
from ..services.backup_mgr import create_db_backup
from ..schemas.all_schemas import SystemSettingsResponse, SystemSettingsUpdate
from .auth import get_current_user

router = APIRouter(prefix="/api/system", tags=["System"])

@router.get("/settings", response_model=SystemSettingsResponse)
async def get_system_settings(db: AsyncSession = Depends(get_db), current_user: User = Depends(get_current_user)):
    stmt = select(SystemSettings).where(SystemSettings.id == 1)
    result = await db.execute(stmt)
    settings = result.scalars().first()

    if not settings:
        settings = SystemSettings(id=1, is_vacation_mode=False, vacation_message="Я в отпуске.")
        db.add(settings)
        await db.commit()
        await db.refresh(settings)

    return settings

@router.post("/settings", response_model=SystemSettingsResponse)
async def update_system_settings(
    settings_data: SystemSettingsUpdate,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    stmt = select(SystemSettings).where(SystemSettings.id == 1)
    result = await db.execute(stmt)
    settings = result.scalars().first()

    if not settings:
        settings = SystemSettings(id=1)
        db.add(settings)

    settings.is_vacation_mode = settings_data.is_vacation_mode
    settings.vacation_end_date = settings_data.vacation_end_date
    settings.vacation_message = settings_data.vacation_message

    await db.commit()
    await db.refresh(settings)
    return settings

@router.get("/export/orders")
async def export_orders_csv(db: AsyncSession = Depends(get_db), current_user: User = Depends(get_current_user)):
    stmt = select(Order).order_by(Order.created_at.desc())
    result = await db.execute(stmt)
    orders = result.scalars().all()
    
    output = io.StringIO()
    writer = csv.writer(output)
    writer.writerow(["ID", "Клиент ID", "Услуга", "Цена", "Статус", "Дата"])
    for order in orders:
        writer.writerow([order.id, order.client_id, order.service_name, order.total_price, order.status, order.created_at.strftime("%Y-%m-%d")])
    
    output.seek(0)
    return StreamingResponse(output, media_type="text/csv", headers={"Content-Disposition": "attachment; filename=orders.csv"})

@router.get("/export/clients")
async def export_clients_csv(db: AsyncSession = Depends(get_db), current_user: User = Depends(get_current_user)):
    stmt = select(Client).order_by(Client.total_spent.desc())
    result = await db.execute(stmt)
    clients = result.scalars().all()
    
    output = io.StringIO()
    writer = csv.writer(output)
    writer.writerow(["ID", "Имя", "VK_ID", "Сегмент", "LTV", "Кэшбэк"])
    for client in clients:
        writer.writerow([client.id, client.name, client.vk_id, client.segment, client.total_spent, client.cashback_balance])
    
    output.seek(0)
    return StreamingResponse(output, media_type="text/csv", headers={"Content-Disposition": "attachment; filename=clients.csv"})

@router.get("/backup/download")
async def download_backup(current_user: User = Depends(get_current_user)):
    backup_path = await create_db_backup()
    if not backup_path:
        raise HTTPException(status_code=500, detail="Backup failed")
    filename = backup_path.split("/")[-1]
    return FileResponse(path=backup_path, media_type="application/octet-stream", filename=filename)
