from contextlib import asynccontextmanager
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
import asyncio
import logging

from .db.session import init_db, close_db
from .api.orders import router as orders_router, action_router as order_actions_router
from .api.clients import router as clients_router
from .api.inventory import router as inventory_router
from .api.chat import router as chat_router
from .api.analytics import router as analytics_router
from .api.system import router as system_router
from .services.vk_bot import bot

# Настройка логгера
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger("main")

vk_task = None


@asynccontextmanager
async def lifespan(app: FastAPI):
    """Управление жизненным циклом приложения (БД и Бот)."""
    global vk_task
    
    logger.info("🚀 Старт системы...")
    
    # Инициализация БД
    await init_db()
    logger.info("✅ База данных готова.")

    # Запуск VK бота в фоне
    if bot:
        logger.info("🤖 Запуск VK-бота...")
        vk_task = asyncio.create_task(bot.run_polling())
    else:
        logger.warning("⚠️ VK-бот не запущен (нет токена).")

    yield

    # Остановка
    logger.info("🛑 Остановка системы...")
    
    if vk_task and not vk_task.done():
        logger.info("Остановка бота...")
        vk_task.cancel()
        try:
            await vk_task
        except asyncio.CancelledError:
            logger.info("Бот остановлен.")
        except Exception as e:
            logger.error(f"Ошибка при остановке бота: {e}")
            
    await close_db()
    logger.info("✅ Система остановлена.")


app = FastAPI(
    title="Лазерная Мастерская CRM",
    description="Полная CRM система с AI и интеграцией ВК",
    version="1.0.0",
    lifespan=lifespan
)

# CORS настройки
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Подключение роутеров
app.include_router(orders_router)
app.include_router(order_actions_router)
app.include_router(clients_router)
app.include_router(inventory_router)
app.include_router(chat_router)
app.include_router(analytics_router)
app.include_router(system_router)


@app.get("/")
async def root():
    return {"status": "running", "service": "Laser CRM API"}


@app.get("/api/ping")
async def ping():
    return {"status": "ok", "version": "1.0.0"}


if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8000)
