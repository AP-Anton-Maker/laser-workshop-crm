import os
import shutil
from datetime import datetime
from pathlib import Path

# Путь к базе данных (должен совпадать с config.py)
# Используем относительный путь от точки запуска или абсолютный, если настроено в env
DB_DIR = Path(__file__).resolve().parent.parent.parent / "data"
DB_FILE = DB_DIR / "laser_crm.sqlite3"
BACKUP_DIR = DB_DIR / "backups"


async def create_db_backup() -> str:
    """
    Создает резервную копию базы данных SQLite.
    
    1. Проверяет существование папки backups, создает при необходимости.
    2. Копирует текущий файл БД с именем backup_YYYYMMDD_HHMMSS.sqlite3.
    3. Возвращает полный путь к созданному файлу.
    
    Raises:
        FileNotFoundError: Если файл базы данных не найден.
        IOError: Если возникли ошибки при копировании (например, файл заблокирован).
    """
    
    # Убедимся, что директория с БД существует
    DB_DIR.mkdir(exist_ok=True)
    
    if not DB_FILE.exists():
        raise FileNotFoundError(f"Файл базы данных не найден: {DB_FILE}")

    # Создаем папку для бэкапов
    BACKUP_DIR.mkdir(exist_ok=True)

    # Генерируем имя файла с текущей датой и временем
    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    backup_filename = f"backup_{timestamp}.sqlite3"
    backup_path = BACKUP_DIR / backup_filename

    try:
        # shutil.copy2 сохраняет метаданные (время модификации), что полезно для аудита
        shutil.copy2(DB_FILE, backup_path)
        print(f"✅ Бэкап успешно создан: {backup_path}")
        return str(backup_path)
        
    except PermissionError:
        raise IOError("Не удалось создать бэкап: файл базы данных заблокирован или нет прав доступа.")
    except Exception as e:
        raise IOError(f"Ошибка при создании бэкапа: {str(e)}")
