"""
Модели данных для CRM системы anton-maker.ru
"""

from .client import Client
from .product import Material, Operation, Product, ProductOperation
from .order import Order
from .inventory import Inventory, InventoryTransaction
from .kpi import ProductionKPI
from .system import QuickReply, Notification, Settings

__all__ = [
    'Client',
    'Material',
    'Operation',
    'Product',
    'ProductOperation',
    'Order',
    'Inventory',
    'InventoryTransaction',
    'ProductionKPI',
    'QuickReply',
    'Notification',
    'Settings',
]
