"""
Django Unfold админка для CRM системы.
Регистрация всех ModelAdmin классов.
"""

from .client_admin import ClientAdmin
from .product_admin import MaterialAdmin, OperationAdmin, ProductAdmin, ProductOperationInline
from .order_admin import OrderAdmin
from .inventory_admin import InventoryAdmin, InventoryTransactionAdmin
from .kpi_admin import ProductionKPIAdmin
from .system_admin import QuickReplyAdmin, NotificationAdmin, SettingsAdmin

__all__ = [
    'ClientAdmin',
    'MaterialAdmin',
    'OperationAdmin',
    'ProductAdmin',
    'ProductOperationInline',
    'OrderAdmin',
    'InventoryAdmin',
    'InventoryTransactionAdmin',
    'ProductionKPIAdmin',
    'QuickReplyAdmin',
    'NotificationAdmin',
    'SettingsAdmin',
]
