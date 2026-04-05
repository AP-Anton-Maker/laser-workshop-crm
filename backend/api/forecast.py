from fastapi import APIRouter, Depends
from sqlalchemy.ext.asyncio import AsyncSession
from typing import Dict, Any

from db.session import get_db
from db.models import User
from api.deps import get_current_active_user
from services.ai import AIForecastService

router = APIRouter(prefix="/api/forecast", tags=["AI Прогнозирование"])

@router.get("/", response_model=Dict[str, Any])
async def get_ai_forecast(
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_active_user)
):
    """
    Получение AI-прогноза выручки на завтрашний день.
    """
    forecast = await AIForecastService.predict_tomorrow_revenue(db)
    return forecast
