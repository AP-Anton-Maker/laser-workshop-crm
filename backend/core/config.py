"""
Конфигурация приложения Laser CRM.
Настройка путей и параметров подключения к базе данных.
"""
import os
from pathlib import Path
from pydantic_settings import BaseSettings


class Settings(BaseSettings):
    """Настройки приложения."""
    
    # Базовая директория проекта (backend)
    BASE_DIR: Path = Path(__file__).resolve().parent.parent
    
    # Директория для данных (находится на уровень выше backend)
    DATA_DIR: Path = BASE_DIR.parent / "data"
    
    # Путь к базе данных SQLite
    # Формат: sqlite+aiosqlite:///../data/laser_crm.sqlite3
    DATABASE_URL: str = f"sqlite+aiosqlite:///{DATA_DIR}/laser_crm.sqlite3"
    
    # Секретный ключ для JWT токенов (в продакшене брать из .env)
    SECRET_KEY: str = "your-secret-key-change-in-production"
    
    # Алгоритм хеширования паролей
    ALGORITHM: str = "HS256"
    
    # Время жизни токена доступа (минуты)
    ACCESS_TOKEN_EXPIRE_MINUTES: int = 60 * 24  # 24 часа
    
    class Config:
        """Конфигурация загрузки настроек."""
        env_file = ".env"
        case_sensitive = True


# Глобальный экземпляр настроек
settings = Settings()

# Создаём директорию data, если она не существует
settings.DATA_DIR.mkdir(parents=True, exist_ok=True)
