from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select
from typing import List
from datetime import datetime

from ..db.session import get_db
from ..db.models import ChatMessage
from ..schemas.chat import MessageSend, ChatHistoryResponse
from ..services.vk_bot import bot  # Импортируем экземпляр бота

router = APIRouter(prefix="/api/chat", tags=["Chat VK"])


@router.get("/history", response_model=List[ChatHistoryResponse])
async def get_chat_history(
    vk_id: int = Query(..., description="ID пользователя ВКонтакте"),
    limit: int = Query(100, description="Количество последних сообщений"),
    db: AsyncSession = Depends(get_db)
):
    """
    Получение истории переписки с конкретным пользователем ВК.
    Возвращает последние N сообщений в хронологическом порядке.
    """
    stmt = (
        select(ChatMessage)
        .where(ChatMessage.vk_id == vk_id)
        .order_by(ChatMessage.timestamp.asc())
        .limit(limit)
    )
    
    result = await db.execute(stmt)
    messages = result.scalars().all()
    
    return messages


@router.post("/send", response_model=ChatHistoryResponse)
async def send_message_to_vk(
    msg_data: MessageSend,
    db: AsyncSession = Depends(get_db)
):
    """
    Отправка сообщения пользователю ВКонтакте из интерфейса CRM.
    1. Сохраняет сообщение в БД (как исходящее от админа).
    2. Отправляет реальное сообщение через API ВК.
    """
    if bot is None:
        raise HTTPException(status_code=503, detail="Сервис ВКонтакте недоступен (нет токена)")

    # 1. Сохраняем в БД
    new_msg = ChatMessage(
        vk_id=msg_data.vk_id,
        is_admin=True,
        message_text=msg_data.message,
        timestamp=datetime.utcnow()
    )
    
    db.add(new_msg)
    await db.commit()
    await db.refresh(new_msg)

    # 2. Отправляем в ВК
    try:
        # peer_id для личного сообщения равен user_id
        await bot.api.messages.send(
            peer_id=msg_data.vk_id,
            message=msg_data.message,
            random_id=0  # Уникальный ID для предотвращения дублей (0 генерируется автоматически в новых версиях, но лучше явно)
        )
    except Exception as e:
        # Если отправка в ВК не удалась, мы все равно сохраняем историю в CRM,
        # но можно записать ошибку в лог или вернуть предупреждение.
        print(f"❌ Ошибка отправки сообщения ВК пользователю {msg_data.vk_id}: {e}")
        # Можно добавить поле error_status в модель, если критично отслеживать доставку
        
    return new_msg
