# ... существующие импорты ...

# ДОБАВИТЬ импорт роутеров
from .api.orders import router as orders_router
from .api.orders import action_router as order_actions_router

# ... внутри функции создания app ...

app = FastAPI(
    title="Лазерная Мастерская CRM",
    description="CRM система для управления заказами, клиентами и складом",
    version="1.0.0",
    lifespan=lifespan
)

# ... middleware CORS ...

# ДОБАВИТЬ подключение роутеров
app.include_router(orders_router)
app.include_router(order_actions_router)

# ... остальной код ...
