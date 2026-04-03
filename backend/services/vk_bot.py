import os
from vkbottle import Bot
from vkbottle.tools import Message
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select
from datetime import datetime

# Импорты наших моделей и сессии
from ..db.models import ChatMessage
from ..db.session import async_session_maker  # Используем фабрику сессий

# Токен берем из переменных окружения
VK_TOKEN = os.getenv("VK_TOKEN", "")

if not VK_TOKEN:
    print("⚠️  ВНИМАНИЕ: VK_TOKEN не найден. Бот ВКонтакте не будет запущен.")
    # Создаем заглушку, чтобы код не падал при отсутствии токена, но предупреждал
    bot = None
else:
    bot = Bot(token=VK_TOKEN)

    @bot.on.message()
    async def handle_message(message: Message):
        """
        Обработчик входящих сообщений от пользователей ВК.
        Сохраняет сообщение в БД и отправляет автоответ.
        """
        if not message.text:
            return

        vk_user_id = message.from_id
        
        # Создаем новую сессию БД специально для этого события бота
        async with async_session_maker() as session:
            try:
                # 1. Сохраняем сообщение от клиента в БД
                new_msg = ChatMessage(
                    vk_id=vk_user_id,
                    is_admin=False,
                    message_text=message.text,
                    timestamp=datetime.utcnow()
                )
                session.add(new_msg)
                await session.commit()
                
                print(f"💬 Сообщение от VK:{vk_user_id} сохранено в БД.")

                # 2. Отправляем автоответ (опционально)
                await message.answer(
                    "Ваше сообщение принято! 🛠\nМастер скоро ответит вам в этом чате."
                )
                
            except Exception as e:
                await session.rollback()
                print(f"❌ Ошибка при сохранении сообщения ВК: {e}")
                # Можно отправить уведомление админу об ошибке, если нужно
