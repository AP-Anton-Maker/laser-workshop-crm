# CRM Admin - Register all ModelAdmin classes

from .client_admin import ClientAdmin
from .product_admin import MaterialAdmin, ServiceOptionAdmin, CalculatorSettingsAdmin
from .order_admin import OrderAdmin
from .kpi_admin import ProductionKPIAdmin

__all__ = [
    'ClientAdmin',
    'MaterialAdmin',
    'ServiceOptionAdmin',
    'CalculatorSettingsAdmin',
    'OrderAdmin',
    'ProductionKPIAdmin',
]
