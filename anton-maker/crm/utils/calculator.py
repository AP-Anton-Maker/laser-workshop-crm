"""
Бэкенд-расчет стоимости заказа.
Используется в калькуляторе и при создании заказов.
"""

from decimal import Decimal
from typing import Optional, Dict, Any
from ..models.product import Material, ServiceOption, CalculatorSettings


class CostCalculator:
    """
    Калькулятор стоимости заказа.
    
    Пример использования:
        calculator = CostCalculator(
            material=material_obj,
            area_cm2=100,
            quantity=2,
            is_urgent=False
        )
        breakdown = calculator.get_breakdown()
    """
    
    def __init__(
        self,
        material: Material,
        area_cm2: float,
        quantity: int = 1,
        is_urgent: bool = False,
        service_options: Optional[list] = None,
    ):
        self.material = material
        self.area_cm2 = Decimal(str(area_cm2))
        self.quantity = quantity
        self.is_urgent = is_urgent
        self.service_options = service_options or []
        self.settings = CalculatorSettings.get()
    
    def calculate_material_cost(self) -> Decimal:
        """
        Расчет стоимости материала.
        
        Формула: Площадь × Цена × (1 + отходы%) × сложность × количество
        """
        total_area = self.area_cm2 * self.quantity
        base_cost = total_area * self.material.price_per_unit
        
        # Применяем коэффициенты
        waste_multiplier = Decimal('1') + self.material.waste_factor / Decimal('100')
        cost = base_cost * waste_multiplier * self.material.complexity_factor
        
        if self.is_urgent:
            cost *= self.settings.rush_multiplier
        
        return cost.quantize(Decimal('0.01'))
    
    def calculate_labor_cost(self) -> Decimal:
        """
        Расчет стоимости работы.
        Упрощенная модель: 10% от стоимости материала за см² обработки.
        """
        # Базовая ставка: 2 ₽ за см² обработки
        labor_rate = Decimal('2')
        total_area = self.area_cm2 * self.quantity
        
        labor_cost = total_area * labor_rate * self.quantity
        
        if self.is_urgent:
            labor_cost *= Decimal('1.5')
        
        return labor_cost.quantize(Decimal('0.01'))
    
    def calculate_overhead(self, base_cost: Decimal) -> Decimal:
        """
        Расчет накладных расходов.
        Обычно 30-40% от прямой себестоимости.
        """
        overhead_rate = Decimal('0.4')
        return (base_cost * overhead_rate).quantize(Decimal('0.01'))
    
    def calculate_defect_reserve(self, base_cost: Decimal) -> Decimal:
        """
        Резерв на брак (2% от себестоимости).
        """
        reserve_rate = Decimal('0.02')
        return (base_cost * reserve_rate).quantize(Decimal('0.01'))
    
    def calculate_services_cost(self, base_cost: Decimal, current_total: Decimal) -> Decimal:
        """Расчет стоимости дополнительных услуг."""
        total_services = Decimal('0')
        
        for option in self.service_options:
            if isinstance(option, ServiceOption):
                total_services += option.calculate_price(base_cost, current_total)
        
        return total_services.quantize(Decimal('0.01'))
    
    def get_sebestoimost(self) -> Decimal:
        """
        Полная себестоимость заказа.
        
        Returns:
            Себестоимость в рублях
        """
        material_cost = self.calculate_material_cost()
        labor_cost = self.calculate_labor_cost()
        base_direct_cost = material_cost + labor_cost
        
        overhead = self.calculate_overhead(base_direct_cost)
        defect_reserve = self.calculate_defect_reserve(base_direct_cost)
        
        return (material_cost + labor_cost + overhead + defect_reserve).quantize(Decimal('0.01'))
    
    def get_retail_price(self) -> Decimal:
        """
        Розничная цена с наценкой.
        
        Returns:
            Розничная цена в рублях
        """
        sebestoimost = self.get_sebestoimost()
        margin_multiplier = Decimal('1') + self.settings.margin_percent / Decimal('100')
        
        price = sebestoimost * margin_multiplier
        
        # Проверка минимального заказа
        if price < self.settings.min_order_amount:
            price = self.settings.min_order_amount
        
        return price.quantize(Decimal('0.01'))
    
    def get_breakdown(self) -> Dict[str, Any]:
        """
        Детализация расчета для отображения клиенту.
        
        Returns:
            Словарь с разбивкой стоимости
        """
        material_cost = self.calculate_material_cost()
        labor_cost = self.calculate_labor_cost()
        base_direct_cost = material_cost + labor_cost
        
        overhead = self.calculate_overhead(base_direct_cost)
        defect_reserve = self.calculate_defect_reserve(base_direct_cost)
        sebestoimost = material_cost + labor_cost + overhead + defect_reserve
        
        margin = self.get_retail_price() - sebestoimost
        
        return {
            'material_cost': material_cost,
            'labor_cost': labor_cost,
            'overhead': overhead,
            'defect_reserve': defect_reserve,
            'sebestoimost': sebestoimost,
            'margin': margin,
            'retail_price': self.get_retail_price(),
            'is_min_order': self.get_retail_price() == self.settings.min_order_amount,
            'min_order_amount': self.settings.min_order_amount,
        }
    
    def get_formatted_breakdown(self) -> str:
        """
        Текстовое представление разбивки стоимости.
        """
        breakdown = self.get_breakdown()
        
        lines = [
            f"📊 Расчет стоимости:",
            f"",
            f"Материал: {breakdown['material_cost']:,.0f} ₽",
            f"Работа: {breakdown['labor_cost']:,.0f} ₽",
            f"Накладные: {breakdown['overhead']:,.0f} ₽",
            f"Резерв на брак: {breakdown['defect_reserve']:,.0f} ₽",
            f"",
            f"Себестоимость: {breakdown['sebestoimost']:,.0f} ₽",
            f"Наценка: {breakdown['margin']:,.0f} ₽",
            f"",
        ]
        
        if breakdown['is_min_order']:
            lines.append(f"⚠️ Применена минимальная стоимость заказа")
            lines.append(f"")
        
        lines.append(f"💰 ИТОГО: {breakdown['retail_price']:,.0f} ₽")
        
        return "\n".join(lines)
