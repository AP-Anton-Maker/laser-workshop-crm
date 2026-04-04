from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select
from datetime import datetime, timedelta
from typing import Optional, Dict, Any
import numpy as np

from ..db.models import Order

try:
    from sklearn.linear_model import LinearRegression
    SKLEARN_AVAILABLE = True
except ImportError:
    SKLEARN_AVAILABLE = False


async def predict_revenue(session: AsyncSession) -> Optional[Dict[str, Any]]:
    """
    Прогнозирует выручку на завтрашний день на основе данных за последние 30 дней.
    """
    if not SKLEARN_AVAILABLE:
        return {"error": "Scikit-learn not installed"}

    thirty_days_ago = datetime.utcnow() - timedelta(days=30)
    
    stmt = (
        select(Order.total_price, Order.updated_at)
        .where(Order.status.in_(["DONE", "COMPLETED"]))
        .where(Order.updated_at >= thirty_days_ago)
        .order_by(Order.updated_at.asc())
    )
    
    result = await session.execute(stmt)
    rows = result.all()
    
    if not rows:
        return None

    daily_revenue: Dict[datetime.date, float] = {}
    
    for price, date_obj in rows:
        if date_obj is None:
            continue
        day_key = date_obj.date()
        daily_revenue[day_key] = daily_revenue.get(day_key, 0.0) + float(price)

    if len(daily_revenue) < 3:
        avg_val = sum(daily_revenue.values()) / len(daily_revenue)
        return {
            "prediction": round(avg_val, 2),
            "trend": "stable",
            "confidence": 0.0,
            "message": "Недостаточно данных для ML-прогноза"
        }

    sorted_days = sorted(daily_revenue.keys())
    X = np.array([[i] for i in range(len(sorted_days))])
    y = np.array([daily_revenue[day] for day in sorted_days])

    model = LinearRegression()
    model.fit(X, y)
    
    next_day_index = len(sorted_days)
    predicted_value = model.predict([[next_day_index]])[0]
    
    slope = model.coef_[0]
    if slope > 500: trend = "up"
    elif slope < -500: trend = "down"
    else: trend = "stable"
        
    confidence = model.score(X, y)
    final_prediction = max(0.0, predicted_value)
    
    return {
        "prediction": round(final_prediction, 2),
        "trend": trend,
        "confidence": round(confidence, 2),
        "message": f"Прогноз на основе {len(sorted_days)} дней"
    }
