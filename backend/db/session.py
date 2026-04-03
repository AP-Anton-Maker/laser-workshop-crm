"""
Асинхронное подключение к базе данных SQLite через SQLAlchemy 2.0.
Используется aiosqlite для асинхронной работы с SQLite.
"""
from sqlalchemy.ext.asyncio import create_async_engine, AsyncSession, async_sessionmaker
from sqlalchemy.orm import declarative_base

from core.config import settings


# Создаём асинхронный движок для подключения к SQLite
# echo=True включает логирование SQL-запросов (отключить в продакшене)
engine = create_async_engine(
    settings.DATABASE_URL,
    echo=False,  # В продакшене установить False
    future=True,  # Используем новый стиль API SQLAlchemy 2.0
)


# Фабрика сессий для создания асинхронных сессий
# expire_on_commit=False предотвращает истечение объектов после коммита
async_session_maker = async_sessionmaker(
    engine,
    class_=AsyncSession,
    expire_on_commit=False,
    autocommit=False,
    autoflush=False,
)


# Базовый класс дляdeclarative моделей
# Все модели будут наследоваться от этого класса
Base = declarative_base()


async def get_db() -> AsyncSession:
    """
    Зависимость FastAPI для получения сессии базы данных.
    Используется в роутах для инъекции сессии.
    
    Пример использования в роуте:
        @app.get("/items")
        async def get_items(db: AsyncSession = Depends(get_db)):
            ...
    """
    async with async_session_maker() as session:
        try:
            yield session
            await session.commit()  # Автоматический коммит при успехе
        except Exception:
            await session.rollback()  # Откат при ошибке
            raise
        finally:
            await session.close()  # Закрываем сессию


async def init_db():
    """
    Инициализация базы данных.
    Создаёт все таблицы, если они не существуют.
    Вызывается при запуске приложения (lifespan event).
    """
    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)


async def close_db():
    """
    Закрытие подключения к базе данных.
    Вызывается при остановке приложения.
    """
    await engine.dispose()
