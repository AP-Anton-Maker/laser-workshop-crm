"""
Утилиты для расчета Lean-метрик производства.
"""

from decimal import Decimal
from datetime import date, timedelta
from typing import Dict, Any


def calculate_oee(
    planned_time: int,
    operating_time: int,
    ideal_cycle_time: Decimal,
    total_count: int,
    good_count: int
) -> Dict[str, Decimal]:
    """
    Рассчитать OEE (Overall Equipment Effectiveness).
    
    Args:
        planned_time: Плановое время работы (минуты)
        operating_time: Фактическое время работы (минуты)
        ideal_cycle_time: Идеальное время цикла на ед. (минуты)
        total_count: Общее количество произведенных единиц
        good_count: Количество годных единиц
        
    Returns:
        dict: Словарь с компонентами OEE в процентах
    """
    # Доступность (Availability)
    if planned_time > 0:
        availability = (Decimal(operating_time) / Decimal(planned_time)) * Decimal('100')
    else:
        availability = Decimal('0')
    
    # Производительность (Performance)
    if operating_time > 0 and ideal_cycle_time > 0:
        ideal_output = Decimal(operating_time) / ideal_cycle_time
        performance = (Decimal(total_count) / ideal_output) * Decimal('100') if ideal_output > 0 else Decimal('0')
    else:
        performance = Decimal('0')
    
    # Качество (Quality)
    if total_count > 0:
        quality = (Decimal(good_count) / Decimal(total_count)) * Decimal('100')
    else:
        quality = Decimal('0')
    
    # OEE = A × P × Q / 10000 (так как все в процентах)
    oee = (availability * performance * quality) / Decimal('10000')
    
    return {
        'availability': availability.quantize(Decimal('0.01')),
        'performance': performance.quantize(Decimal('0.01')),
        'quality': quality.quantize(Decimal('0.01')),
        'oee': oee.quantize(Decimal('0.01')),
    }


def calculate_waste_percentage(
    total_material: Decimal,
    waste_material: Decimal
) -> Decimal:
    """
    Рассчитать процент отходов.
    
    Args:
        total_material: Общее количество материала
        waste_material: Количество отходов
        
    Returns:
        Decimal: Процент отходов
    """
    if total_material > 0:
        percentage = (waste_material / total_material) * Decimal('100')
        return percentage.quantize(Decimal('0.01'))
    return Decimal('0.00')


def calculate_lead_time(
    start_date: date,
    end_date: date,
    exclude_weekends: bool = True
) -> int:
    """
    Рассчитать время выполнения заказа в часах.
    
    Args:
        start_date: Дата начала
        end_date: Дата окончания
        exclude_weekends: Исключить выходные
        
    Returns:
        int: Время в часах
    """
    if start_date > end_date:
        return 0
    
    delta = end_date - start_date
    total_hours = delta.days * 24 + delta.seconds // 3600
    
    if exclude_weekends:
        # Упрощенный расчет: вычитаем выходные
        weekends = 0
        current = start_date
        while current < end_date:
            if current.weekday() >= 5:  # Суббота или Воскресенье
                weekends += 1
            current += timedelta(days=1)
        
        total_hours -= weekends * 24 * 2  # 24 часа × 2 выходных дня
    
    return max(0, total_hours)


def get_daily_production_summary(target_date: date = None) -> Dict[str, Any]:
    """
    Получить сводку производства за день.
    
    Args:
        target_date: Дата отчета (по умолчанию сегодня)
        
    Returns:
        dict: Сводка с метриками
    """
    from crm.models import Order, ProductionKPI
    
    if target_date is None:
        target_date = date.today()
    
    # Заказы за день
    orders_created = Order.objects.filter(
        created_at__date=target_date
    ).count()
    
    orders_completed = Order.objects.filter(
        completed_at__date=target_date
    ).count()
    
    # WIP (Work In Progress)
    wip_count = Order.objects.filter(
        status='IN_PROGRESS'
    ).count()
    
    # Среднее время выполнения
    completed_orders = Order.objects.filter(
        completed_at__date=target_date,
        started_at__isnull=False,
        completed_at__isnull=False
    )
    
    avg_lead_time = 0
    if completed_orders.exists():
        total_hours = sum(
            order.get_lead_time_hours() or 0 
            for order in completed_orders
        )
        avg_lead_time = total_hours / completed_orders.count()
    
    return {
        'date': target_date,
        'orders_created': orders_created,
        'orders_completed': orders_completed,
        'wip_count': wip_count,
        'avg_lead_time_hours': round(avg_lead_time, 2),
    }
