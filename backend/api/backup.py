import os
from fastapi import APIRouter, Depends, HTTPException
from fastapi.responses import FileResponse
from sqlalchemy.ext.asyncio import AsyncSession

from db.session import get_db
from db.models import User
from api.deps import get_current_active_user
from services.backup import BackupService

router = APIRouter(prefix="/api/backup", tags=["Резервное копирование"])

@router.get("/download")
async def download_backup(
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_active_user)
):
    """
    Генерация и скачивание полного ZIP-бэкапа системы.
    Доступно только администраторам.
    """
    if not current_user.is_superuser:
        raise HTTPException(status_code=403, detail="Доступно только администратору")
        
    zip_path = await BackupService.create_full_backup(db)
    
    if not os.path.exists(zip_path):
        raise HTTPException(status_code=500, detail="Ошибка при формировании архива")
        
    return FileResponse(
        path=zip_path, 
        filename=os.path.basename(zip_path),
        media_type="application/zip",
        background=None # В реальном продакшене тут ставится BackgroundTask для удаления файла после скачивания
    )
