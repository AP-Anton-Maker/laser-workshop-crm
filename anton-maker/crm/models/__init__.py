# CRM Models - Import all models for easy access

from .client import Client
from .product import Material, ServiceOption, CalculatorSettings
from .order import Order
from .kpi import ProductionKPI

__all__ = [
    'Client',
    'Material',
    'ServiceOption',
    'CalculatorSettings',
    'Order',
    'ProductionKPI',
]
