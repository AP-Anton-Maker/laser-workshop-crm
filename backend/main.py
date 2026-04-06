import os
import asyncio
from contextlib import asynccontextmanager
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from fastapi.staticfiles import StaticFiles

from core.config import settings
from db.session import engine, Base, async_session_maker
from api.auth import router as auth_router, create_default_admin
from api.clients import router as clients_router
from api.orders import router as orders_router
from api.inventory import router as inventory_router
from api.calculator import router as calculator_router
from api.forecast import router as forecast_router
from api.backup import router as backup_router
from api.chat import router as chat_router
from services.vk_bot import bot

@asynccontextmanager
async def lifespan(app: FastAPI):
    """
    Жизненный цикл FastAPI приложения. Выполняется при старте сервера.
    Здесь инициализируется БД и запускаются фоновые процессы.
    """
    # 1. Создание всех таблиц в БД (если их нет)
    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)
        
    # 2. Создание пользователя admin (по умолчанию)
    async with async_session_maker() as session:
        await create_default_admin(session)
        
    # 3. Запуск фонового процесса VK Бота (Long Poll)
    bot_task = None
    if bot:
        bot_task = asyncio.create_task(bot.run_polling())
        
    yield # --- Приложение работает в этот момент ---
    
    # 4. Грациозное завершение работы при остановке сервера
    if bot_task:
        bot_task.cancel()
    await engine.dispose()

# Инициализация приложения
app = FastAPI(
    title=settings.PROJECT_NAME,
    version="1.0.0",
    description="Enterprise CRM для лазерной мастерской",
    lifespan=lifespan
)

# Настройка CORS (разрешаем запросы откуда угодно)
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Подключение всех API роутеров (Сборка API)
app.include_router(auth_router, prefix="/api")
app.include_router(clients_router, prefix="/api")
app.include_router(orders_router, prefix="/api")
app.include_router(inventory_router, prefix="/api")
app.include_router(calculator_router, prefix="/api")
app.include_router(forecast_router, prefix="/api")
app.include_router(backup_router, prefix="/api")
app.include_router(chat_router, prefix="/api")

# Настройка раздачи статики (Фронтенда)
# Вычисляем путь к папке frontend (она находится на уровень выше папки backend)
BASE_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
FRONTEND_DIR = os.path.join(BASE_DIR, "frontend")

# Если папки frontend еще нет (например, при первом запуске бэкенда), создаем её,
# чтобы FastAPI не выдал ошибку RuntimeError: Directory does not exist
os.makedirs(FRONTEND_DIR, exist_ok=True)

# Монтируем корневой маршрут "/" для отдачи HTML/CSS/JS (SPA)
app.mount("/", StaticFiles(directory=FRONTEND_DIR, html=True), name="frontend")
