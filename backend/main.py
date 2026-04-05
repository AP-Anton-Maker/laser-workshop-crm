from contextlib import asynccontextmanager
from fastapi.staticfiles import StaticFiles
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
import asyncio
import logging

from .db.session import init_db, close_db
from .api.auth import router as auth_router, create_default_admin
from .api.orders import router as orders_router, action_router as order_actions_router
from .api.clients import router as clients_router
from .api.inventory import router as inventory_router
from .api.chat import router as chat_router
from .api.analytics import router as analytics_router
from .api.system import router as system_router
from .services.vk_bot import bot
from api.calculator import router as calculator_router
from api.forecast import router as forecast_router
from api.backup import router as backup_router

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger("main")

vk_task = None

@asynccontextmanager
async def lifespan(app: FastAPI):
    global vk_task
    logger.info("🚀 Starting Laser CRM...")
    
    # Init DB
    await init_db()
    logger.info("✅ Database initialized")
    
    # Create Default Admin
    async with asyncio.create_task(asyncio.sleep(0)).get_loop().create_task(asyncio.sleep(0)).get_loop().create_task(asyncio.sleep(0)): # Hack to get loop context if needed, but simpler:
        async with app.state.db_session_maker() as session: # Wait, we need session here. Let's use direct engine connection or helper.
            # Correct way using session maker directly imported or via app state if set. 
            # Since get_db is a generator, let's use async_session_maker directly for startup tasks.
            from .db.session import async_session_maker
            async with async_session_maker() as session:
                await create_default_admin(session)

    # Start VK Bot
    if bot:
        logger.info("🤖 Starting VK Bot...")
        vk_task = asyncio.create_task(bot.run_polling())
    else:
        logger.warning("⚠️ VK Bot skipped (no token)")

    yield

    logger.info("🛑 Shutting down...")
    if vk_task and not vk_task.done():
        vk_task.cancel()
        try:
            await vk_task
        except asyncio.CancelledError:
            pass
    await close_db()
    logger.info("✅ Shutdown complete")

app = FastAPI(title="Laser CRM", lifespan=lifespan)

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Routers
app.include_router(auth_router)
app.include_router(orders_router)
app.include_router(order_actions_router)
app.include_router(clients_router)
app.include_router(inventory_router)
app.include_router(chat_router)
app.include_router(analytics_router)
app.include_router(system_router)
app.include_router(calculator_router)
app.include_router(forecast_router)
app.include_router(backup_router)

@app.get("/")
async def root():
    return {"status": "running", "service": "Laser CRM API"}

@app.get("/api/ping")
async def ping():
    return {"status": "ok"}

import os
frontend_path = os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), "frontend")
app.mount("/", StaticFiles(directory=frontend_path, html=True), name="frontend")

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8000)
