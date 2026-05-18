"""
Ядро расчета себестоимости продукции.
Используется для автоматического расчета цен на изделия.
"""

from decimal import Decimal
from typing import Dict, Any
from crm.models import Product


class CostCalculator:
    """
    Калькулятор стоимости изделия.
    
    Рассчитывает полную себестоимость с учетом:
    - Материала (с отходами)
    - Работы (наладка + время на ед.)
    - Накладных расходов
    - Резерва на брак
    - Наценки
    """
    
    def __init__(
        self,
        product: Product,
        quantity: int = 1,
        urgency: str = 'standard'
    ):
        """
        Инициализация калькулятора.
        
        Args:
            product: Изделие для расчета
            quantity: Количество изделий
            urgency: Срочность ('standard', 'express', 'super_express')
        """
        self.product = product
        self.quantity = quantity
        self.urgency = urgency
        
        # Коэффициенты срочности
        self.urgency_coefficients = {
            'standard': Decimal('1.0'),
            'express': Decimal('1.3'),
            'super_express': Decimal('1.5'),
        }
        
        # Ставки накладных расходов (40% от прямых затрат)
        self.overhead_rate = Decimal('0.4')
        
        # Резерв на брак (2%)
        self.defect_rate = Decimal('0.02')
        
        # Базовая наценка (50%)
        self.base_markup_rate = Decimal('0.5')
    
    def calculate_material_cost(self) -> Decimal:
        """
        Рассчитать стоимость материала с учетом отходов.
        
        Returns:
            Decimal: Стоимость материала
        """
        if not self.product.material:
            return Decimal('0.00')
        
        material = self.product.material
        
        # Вес одного изделия
        weight = self.product.calculate_net_weight_kg()
        
        # Учет отходов
        waste_multiplier = Decimal('1') + material.waste_factor / Decimal('100')
        
        # Общая стоимость материала
        cost = (
            weight * 
            material.price_per_unit * 
            waste_multiplier * 
            self.quantity
        )
        
        return cost.quantize(Decimal('0.01'))
    
    def calculate_labor_cost(self) -> Decimal:
        """
        Рассчитать стоимость работ.
        
        Returns:
            Decimal: Стоимость работ
        """
        total_labor_cost = Decimal('0.00')
        
        # Получаем все операции для изделия
        product_ops = self.product.product_operations.select_related('operation').all()
        
        for prod_op in product_ops:
            operation = prod_op.operation
            
            # Время наладки (единовременно на партию)
            setup_hours = Decimal(operation.setup_time_min) / Decimal('60')
            setup_cost = setup_hours * operation.hourly_rate
            
            # Время на выполнение (на каждое изделие)
            time_per_unit_hours = prod_op.time_per_unit_min / Decimal('60')
            execution_cost = time_per_unit_hours * operation.hourly_rate * self.quantity
            
            total_labor_cost += setup_cost + execution_cost
        
        return total_labor_cost.quantize(Decimal('0.01'))
    
    def calculate_overhead(self, direct_costs: Decimal = None) -> Decimal:
        """
        Рассчитать накладные расходы.
        
        Args:
            direct_costs: Прямые затраты (материал + работа). 
                         Если None, будет рассчитано автоматически.
        
        Returns:
            Decimal: Сумма накладных расходов
        """
        if direct_costs is None:
            material_cost = self.calculate_material_cost()
            labor_cost = self.calculate_labor_cost()
            direct_costs = material_cost + labor_cost
        
        overhead = direct_costs * self.overhead_rate
        return overhead.quantize(Decimal('0.01'))
    
    def calculate_defect_reserve(self, base_cost: Decimal = None) -> Decimal:
        """
        Рассчитать резерв на брак.
        
        Args:
            base_cost: Базовая стоимость для расчета резерва.
                      Если None, будет рассчитана себестоимость.
        
        Returns:
            Decimal: Резерв на брак
        """
        if base_cost is None:
            base_cost = self.get_sebestoimost_without_defect()
        
        reserve = base_cost * self.defect_rate
        return reserve.quantize(Decimal('0.01'))
    
    def get_sebestoimost_without_defect(self) -> Decimal:
        """Получить себестоимость без учета резерва на брак."""
        material_cost = self.calculate_material_cost()
        labor_cost = self.calculate_labor_cost()
        overhead = self.calculate_overhead(material_cost + labor_cost)
        
        return material_cost + labor_cost + overhead
    
    def get_sebestoimost(self) -> Decimal:
        """
        Получить полную себестоимость (с резервом на брак).
        
        Returns:
            Decimal: Полная себестоимость
        """
        base_cost = self.get_sebestoimost_without_defect()
        defect_reserve = self.calculate_defect_reserve(base_cost)
        
        return (base_cost + defect_reserve).quantize(Decimal('0.01'))
    
    def get_retail_price(self) -> Decimal:
        """
        Получить розничную цену (себестоимость + наценка).
        
        Returns:
            Decimal: Розничная цена
        """
        sebestoimost = self.get_sebestoimost()
        
        # Базовая наценка
        markup = sebestoimost * self.base_markup_rate
        
        # Корректировка на срочность
        urgency_coef = self.urgency_coefficients.get(
            self.urgency, 
            Decimal('1.0')
        )
        
        retail_price = (sebestoimost + markup) * urgency_coef
        
        return retail_price.quantize(Decimal('0.01'))
    
    def get_breakdown(self) -> Dict[str, Any]:
        """
        Получить детальную разбивку стоимости.
        
        Returns:
            dict: Словарь с детализацией по статьям затрат
        """
        material_cost = self.calculate_material_cost()
        labor_cost = self.calculate_labor_cost()
        direct_costs = material_cost + labor_cost
        overhead = self.calculate_overhead(direct_costs)
        base_cost = direct_costs + overhead
        defect_reserve = self.calculate_defect_reserve(base_cost)
        sebestoimost = base_cost + defect_reserve
        
        markup = sebestoimost * self.base_markup_rate
        urgency_coef = self.urgency_coefficients.get(self.urgency, Decimal('1.0'))
        retail_price = (sebestoimost + markup) * urgency_coef
        
        return {
            'material_cost': float(material_cost),
            'labor_cost': float(labor_cost),
            'direct_costs': float(direct_costs),
            'overhead': float(overhead),
            'defect_reserve': float(defect_reserve),
            'sebestoimost': float(sebestoimost),
            'markup': float(markup),
            'urgency_coefficient': float(urgency_coef),
            'retail_price': float(retail_price),
            
            # Дополнительные данные
            'quantity': self.quantity,
            'urgency': self.urgency,
            'price_per_unit': float(retail_price / self.quantity) if self.quantity > 0 else 0,
        }
