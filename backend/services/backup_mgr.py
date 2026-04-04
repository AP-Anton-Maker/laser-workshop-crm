import shutil
import os
from pathlib import Path
from datetime import datetime
from typing import Optional

async def create_db_backup() -> Optional[str]:
    """
    Создает резервную копию файла базы данных SQLite.
    
    :return: Абсолютный путь к созданному файлу бэкапа или None в случае ошибки.
    """
    # Пути (относительно расположения этого файла или проекта)
    # Предполагаем структуру: backend/services/backup_mgr.py -> ../data/laser_crm.sqlite3
    current_dir = Path(__file__).resolve().parent
    project_root = current_dir.parent.parent
    
    db_rel_path = "../data/laser_crm.sqlite3"
    backups_rel_path = "../data/backups"
    
    db_source = (project_root / db_rel_path).resolve()
    backup_dir = (project_root / backups_rel_path).resolve()
    
    # Проверка существования исходного файла
    if not db_source.exists():
        raise FileNotFoundError(f"Файл базы данных не найден: {db_source}")

    # Создание директории для бэкапов, если нет
    backup_dir.mkdir(parents=True, exist_ok=True)
    
    # Генерация имени файла с таймстемпом
    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    backup_filename = f"backup_{timestamp}.sqlite3"
    backup_dest = backup_dir / backup_filename
    
    try:
        # Копирование файла с сохранением метаданных
        shutil.copy2(db_source, backup_dest)
        return str(backup_dest.resolve())
    except PermissionError as pe:
        raise PermissionError(f"Нет прав доступа к файлу БД для копирования: {pe}")
    except Exception as e:
        raise RuntimeError(f"Ошибка при создании бэкапа: {e}")
