from pydantic_settings import BaseSettings
from pathlib import Path
import os


class Settings(BaseSettings):
    """
    Конфигурация приложения.
    Загружает переменные окружения или использует значения по умолчанию.
    """
    # URL базы данных
    DATABASE_URL: str = "sqlite+aiosqlite:///../data/laser_crm.sqlite3"
    
    # Токен группы ВКонтакте
    VK_TOKEN: str = os.getenv("VK_TOKEN", "")
    
    # Секретный ключ для сессий (опционально)
    SECRET_KEY: str = "super_secret_key_change_me_in_prod"

    class Config:
        env_file = ".env"
        extra = "ignore"

    @property
    def database_path_resolved(self) -> str:
        """
        Возвращает путь к БД, предварительно создав директорию, если её нет.
        """
        # Извлекаем относительный путь из строки подключения
        # sqlite+aiosqlite:///../data/file.db -> ../data/file.db
        path_str = self.DATABASE_URL.replace("sqlite+aiosqlite:///", "")
        db_path = Path(path_str)
        
        # Создаем директорию
        db_dir = db_path.parent
        if not db_dir.exists():
            db_dir.mkdir(parents=True, exist_ok=True)
            
        return self.DATABASE_URL


settings = Settings()
