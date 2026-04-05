from fastapi import APIRouter, Depends
from services.calculator import CalculatorService, CalcRequest
from db.models import User
from api.deps import get_current_active_user
from typing import Dict, Any

router = APIRouter(prefix="/api/calculator", tags=["Калькулятор заказов"])

@router.post("/calculate", response_model=Dict[str, Any])
async def calculate_price(
    request: CalcRequest,
    current_user: User = Depends(get_current_active_user)
):
    """
    Расчет стоимости заказа по 11 различным алгоритмам.
    Доступно только авторизованным менеджерам/админам.
    """
    result = CalculatorService.calculate(request)
    return result
