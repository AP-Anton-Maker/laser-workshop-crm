import os
from fastapi import APIRouter, Depends, BackgroundTasks
from fastapi.responses import FileResponse
from sqlalchemy.ext.asyncio import AsyncSession

from db.session import get_db
from db.models import User
from api.deps import get_current_active_user
from services.backup import BackupService

router = APIRouter(prefix="/backup", tags=["Бэкапы"])

def cleanup_backup_file(filepath: str):
    """Фоновая задача для удаления ZIP-архива после его скачивания клиентом."""
    if os.path.exists(filepath):
        os.remove(filepath)

@router.get("/download")
async def download_backup(
    background_tasks: BackgroundTasks,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_active_user)
):
    """
    Создает полный дамп базы (CSV + SQLite в ZIP-архиве) 
    и возвращает его как скачиваемый файл. 
    После скачивания архив автоматически удаляется с диска сервера.
    """
    zip_filepath = await BackupService.create_full_backup(db)
    
    # Добавляем задачу удаления файла в фон
    background_tasks.add_task(cleanup_backup_file, zip_filepath)
    
    filename = os.path.basename(zip_filepath)
    return FileResponse(
        path=zip_filepath, 
        filename=filename, 
        media_type="application/zip"
    )
