from pydantic import BaseModel, Field, ConfigDict
from datetime import datetime
from typing import Optional


class MessageSend(BaseModel):
    """Схема для отправки сообщения админом через CRM"""
    vk_id: int = Field(..., description="ID пользователя ВКонтакте")
    message: str = Field(..., min_length=1, description="Текст сообщения")


class ChatHistoryResponse(BaseModel):
    """Схема ответа истории переписки"""
    id: int
    vk_id: int
    is_admin: bool
    message_text: str
    timestamp: datetime

    model_config = ConfigDict(from_attributes=True)
