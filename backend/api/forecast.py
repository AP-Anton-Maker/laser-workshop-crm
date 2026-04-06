from typing import Dict, Any
from fastapi import APIRouter, Depends
from sqlalchemy.ext.asyncio import AsyncSession

from db.session import get_db
from db.models import User
from api.deps import get_current_active_user
from services.ai import AIForecastService

router = APIRouter(prefix="/forecast", tags=["Аналитика и AI"])

@router.get("/")
async def get_forecast(
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_active_user)
) -> Dict[str, Any]:
    """
    Вызывает AI-сервис (scikit-learn) для анализа выручки 
    за последние 30 дней и построения прогноза на завтра.
    """
    forecast_data = await AIForecastService.predict_tomorrow_revenue(db)
    return forecast_data
