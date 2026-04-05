from enum import Enum
from pydantic import BaseModel
from typing import Optional, Dict, Any

class CalcMethod(str, Enum):
    AREA = "area"                   # 1. По площади (кв. см / кв. м)
    PERIMETER = "perimeter"         # 2. По длине реза (периметр)
    TIME = "time"                   # 3. По времени работы станка
    ENGRAVING = "engraving"         # 4. Гравировка (попиксельная/площадь)
    VOLUME_3D = "volume_3d"         # 5. 3D фрезеровка/лазер (объем)
    WEIGHT = "weight"               # 6. По весу материала (для специфичных задач)
    FIXED = "fixed"                 # 7. Фиксированная стоимость (дизайн, макет)
    WHOLESALE = "wholesale"         # 8. Оптовая партия (динамическая скидка)
    RUSH_ORDER = "rush_order"       # 9. Срочный заказ (коэффициент наценки)
    MATERIAL_ONLY = "material"      # 10. Только продажа материала (без резки)
    COMPLEX = "complex"             # 11. Комбинированный (Материал + Резка + Срочность)

class CalcRequest(BaseModel):
    method: CalcMethod
    width_mm: float = 0.0
    height_mm: float = 0.0
    length_mm: float = 0.0       # Для периметра или 3D
    thickness_mm: float = 0.0    # Толщина материала
    time_minutes: float = 0.0
    weight_kg: float = 0.0
    quantity: int = 1
    material_cost_per_unit: float = 0.0
    base_rate: float = 0.0       # Базовая ставка (за метр, за минуту и т.д.)
    is_rush: bool = False        # Срочность
    
class CalculatorService:
    MIN_ORDER_PRICE = 500.0      # Минимальная стоимость любого заказа
    RUSH_MULTIPLIER = 1.5        # Наценка 50% за срочность
    
    @staticmethod
    def calculate(data: CalcRequest) -> Dict[str, Any]:
        cost = 0.0
        
        # --- Алгоритмы ---
        if data.method == CalcMethod.AREA:
            # Перевод в кв. метры (если нужно) или считаем в кв. мм
            area_m2 = (data.width_mm * data.height_mm) / 1_000_000
            cost = area_m2 * data.base_rate
            
        elif data.method == CalcMethod.PERIMETER:
            # Базовая ставка за метр реза
            length_m = data.length_mm / 1000
            cost = length_m * data.base_rate * data.thickness_mm # Учет толщины
            
        elif data.method == CalcMethod.TIME:
            cost = data.time_minutes * data.base_rate
            
        elif data.method == CalcMethod.ENGRAVING:
            area_cm2 = (data.width_mm * data.height_mm) / 100
            cost = area_cm2 * data.base_rate
            
        elif data.method == CalcMethod.VOLUME_3D:
            volume_cm3 = (data.width_mm * data.height_mm * data.thickness_mm) / 1000
            cost = volume_cm3 * data.base_rate
            
        elif data.method == CalcMethod.WEIGHT:
            cost = data.weight_kg * data.base_rate
            
        elif data.method == CalcMethod.FIXED:
            cost = data.base_rate
            
        elif data.method == CalcMethod.MATERIAL_ONLY:
            cost = data.material_cost_per_unit
            
        elif data.method == CalcMethod.WHOLESALE:
            # Чем больше количество, тем меньше ставка
            discount = 0.0
            if data.quantity >= 100: discount = 0.20 # 20% скидка
            elif data.quantity >= 50: discount = 0.10 # 10% скидка
            base_cost = data.base_rate * data.quantity
            cost = base_cost - (base_cost * discount)
            # В этом методе quantity уже учтено, поэтому ставим 1 для финального умножения
            data.quantity = 1 
            
        elif data.method == CalcMethod.COMPLEX:
            # Материал + Работа (периметр)
            length_m = data.length_mm / 1000
            work_cost = length_m * data.base_rate
            material_cost = data.material_cost_per_unit
            cost = work_cost + material_cost

        # Умножаем на количество (если это не опт, где мы уже учли)
        total_price = cost * data.quantity
        
        # Наценка за срочность
        if data.is_rush:
            total_price *= CalculatorService.RUSH_MULTIPLIER
            
        # Защита: не ниже минимальной стоимости заказа
        final_price = max(total_price, CalculatorService.MIN_ORDER_PRICE)
        
        return {
            "method": data.method,
            "raw_cost": round(total_price, 2),
            "final_price": round(final_price, 2),
            "is_min_price_applied": final_price == CalculatorService.MIN_ORDER_PRICE,
            "currency": "RUB"
        }
