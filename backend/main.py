# Импорты сессий и роутеров
import asyncio
from contextlib import asynccontextmanager
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from .db.session import init_db, close_db
from .api.orders import router as orders_router
from .api.orders import action_router as order_actions_router
from .api.chat import router as chat_router
from .api.inventory import router as inventory_router
from .api.clients import router as clients_router

# Импорт бота
from .services.vk_bot import bot

# Глобальная переменная для задачи бота
vk_polling_task = None


@asynccontextmanager
async def lifespan(app: FastAPI):
    """Lifespan событие для инициализации БД и запуска VK-бота в фоне"""
    global vk_polling_task
    
    print("🚀 Инициализация системы...")
    
    # 1. Инициализация БД
    await init_db()
    print("✅ База данных инициализирована!")

    # 2. Запуск VK-бота в фоновом режиме (если токен настроен)
    if bot:
        print("🤖 Запуск VK-бота в фоновом режиме...")
        # bot.run_polling() - это бесконечный цикл, поэтому запускаем как задачу
        vk_polling_task = asyncio.create_task(bot.run_polling())
    else:
        print("⚠️  VK-бот пропущен (отсутствует токен).")

    yield  # Сервер работает

    # --- Завершение работы ---
    print("🛑 Остановка системы...")
    
    # Отменяем задачу бота, если она существует
    if vk_polling_task and not vk_polling_task.done():
        print("Остановка VK-поллинга...")
        vk_polling_task.cancel()
        try:
            await vk_polling_task
        except asyncio.CancelledError:
            pass  # Ожидаемая ошибка при отмене
            
    # Закрытие соединений с БД
    await close_db()
    print("✅ Система остановлена.")


app = FastAPI(
    title="Лазерная Мастерская CRM",
    description="CRM система с интеграцией ВКонтакте",
    version="1.0.0",
    lifespan=lifespan
)

# Настройка CORS
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
app.include_router(chat_router)  # <--- Роутер чата
app.include_router(inventory_router)  # <-- Роутер инвентаря
app.include_router(clients_router)  # <-- Роутер клиента

@app.get("/")
async def root():
    return {"message": "Добро пожаловать в Лазерную Мастерскую CRM!"}


@app.get("/api/ping")
async def ping():
    return {
        "status": "ok",
        "message": "🔬 Laser CRM API + VK Bot работает!",
        "version": "1.0.0"
    }


if __name__ == "__main__":
    import uvicorn
    # Запускаем сервер
    uvicorn.run(app, host="0.0.0.0", port=8000)
