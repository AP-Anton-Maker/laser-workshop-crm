import random
from typing import List
from pydantic import BaseModel
from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.future import select

from db.session import get_db
from db.models import User, Client, ChatMessage, ChatDirection
from schemas import ChatMessageResponse
from api.deps import get_current_active_user
from services.vk_bot import bot

router = APIRouter(prefix="/chat", tags=["VK Чат"])

class SendMessageRequest(BaseModel):
    text: str

@router.get("/{client_id}", response_model=List[ChatMessageResponse])
async def get_chat_history(
    client_id: int,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_active_user)
):
    """
    Возвращает историю сообщений с клиентом.
    Все входящие непрочитанные сообщения автоматически помечаются как прочитанные.
    """
    client = await db.get(Client, client_id)
    if not client:
        raise HTTPException(status_code=404, detail="Клиент не найден")

    # Помечаем непрочитанные сообщения как прочитанные
    stmt_unread = select(ChatMessage).where(
        ChatMessage.client_id == client_id,
        ChatMessage.direction == ChatDirection.IN,
        ChatMessage.is_read == False
    )
    result_unread = await db.execute(stmt_unread)
    unread_messages = result_unread.scalars().all()
    
    for msg in unread_messages:
        msg.is_read = True
        
    if unread_messages:
        await db.commit()

    # Получаем всю историю, сортируя по дате по возрастанию (старые сверху, новые снизу)
    stmt_history = select(ChatMessage).where(
        ChatMessage.client_id == client_id
    ).order_by(ChatMessage.timestamp.asc())
    
    result_history = await db.execute(stmt_history)
    return result_history.scalars().all()

@router.post("/{client_id}/send", response_model=ChatMessageResponse)
async def send_message(
    client_id: int,
    payload: SendMessageRequest,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_active_user)
):
    """
    Отправляет сообщение клиенту через VK API и сохраняет его в базе.
    """
    client = await db.get(Client, client_id)
    if not client:
        raise HTTPException(status_code=404, detail="Клиент не найден")
        
    if not client.vk_id:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST, 
            detail="У этого клиента нет привязанного VK ID"
        )

    # Отправка сообщения в ВК
    if bot:
        try:
            await bot.api.messages.send(
                user_id=client.vk_id,
                message=payload.text,
                random_id=random.randint(1, 2**31) # Требование VK API
            )
        except Exception as e:
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail=f"Ошибка отправки сообщения в VK: {str(e)}"
            )
    else:
        # Для локального тестирования без токена
        pass

    # Сохранение в БД
    new_msg = ChatMessage(
        client_id=client_id,
        direction=ChatDirection.OUT,
        text=payload.text,
        is_read=True
    )
    db.add(new_msg)
    await db.commit()
    await db.refresh(new_msg)
    
    return new_msg
