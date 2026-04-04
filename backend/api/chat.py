from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select
from typing import List
from datetime import datetime

from ..db.session import get_db
from ..db.models import ChatMessage, User
from ..schemas.all_schemas import MessageSend, ChatHistoryResponse
from ..services.vk_bot import bot
from .auth import get_current_user

router = APIRouter(prefix="/api/chat", tags=["Chat"])

@router.get("/history", response_model=List[ChatHistoryResponse])
async def get_history(vk_id: int, db: AsyncSession = Depends(get_db), current_user: User = Depends(get_current_user)):
    stmt = select(ChatMessage).where(ChatMessage.vk_id == vk_id).order_by(ChatMessage.timestamp.asc()).limit(100)
    result = await db.execute(stmt)
    return result.scalars().all()

@router.post("/send", response_model=ChatHistoryResponse)
async def send_msg(msg_data: MessageSend, db: AsyncSession = Depends(get_db), current_user: User = Depends(get_current_user)):
    if not bot:
        raise HTTPException(503, "VK Bot not running")
    
    new_msg = ChatMessage(vk_id=msg_data.vk_id, is_admin=True, message_text=msg_data.message)
    db.add(new_msg)
    await db.commit()
    await db.refresh(new_msg)
    
    try:
        await bot.api.messages.send(peer_id=msg_data.vk_id, message=msg_data.message, random_id=0)
    except Exception as e:
        print(f"VK Send Error: {e}")
        
    return new_msg
