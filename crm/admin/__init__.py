# Импорт всех админ-классов для регистрации через декораторы @admin.register
from .client_admin import ClientAdmin
from .inventory_admin import MaterialAdmin
from .order_admin import OrderAdmin
from .system_admin import QuickReplyAdmin
from .calculator_view import custom_calculator_view

__all__ = [
    "ClientAdmin",
    "MaterialAdmin",
    "OrderAdmin",
    "QuickReplyAdmin",
    "custom_calculator_view",
]
