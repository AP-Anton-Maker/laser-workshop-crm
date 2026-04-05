from pydantic_settings import BaseSettings
from typing import Optional

class Settings(BaseSettings):
    # Базовые настройки
    project_name: str = "Laser CRM"
    
    # База данных (путь по умолчанию, если нет .env)
    database_url: str = "sqlite+aiosqlite:///../data/laser_crm.sqlite3"
    
    # Безопасность
    secret_key: str = "super_secret_key_change_me_in_production"
    algorithm: str = "HS256"
    access_token_expire_minutes: int = 10080  # Токен живет 7 дней
    
    # ВКонтакте
    vk_token: str = ""

    class Config:
        env_file = ".env"
        env_file_encoding = "utf-8"
        extra = "ignore"

settings = Settings()
