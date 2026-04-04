from sqlalchemy import Column, Integer, String, Text, Float, DateTime, Boolean, ForeignKey
from sqlalchemy.orm import relationship
from datetime import datetime
from .session import Base


class User(Base):
    """Пользователи системы (Админы, Менеджеры)"""
    __tablename__ = "users"

    id = Column(Integer, primary_key=True, index=True)
    username = Column(String(50), unique=True, index=True, nullable=False)
    password_hash = Column(String(255), nullable=False)
    role = Column(String(20), default="manager", nullable=False)  # admin, manager
    created_at = Column(DateTime, default=datetime.utcnow)
    is_active = Column(Boolean, default=True)

    orders = relationship("Order", back_populates="user")
    audit_logs = relationship("AuditLog", back_populates="user")


class Client(Base):
    """Клиенты и система лояльности"""
    __tablename__ = "clients"

    id = Column(Integer, primary_key=True, index=True)
    name = Column(String(100), nullable=False)
    vk_id = Column(String(50), index=True)  # ID ВКонтакте
    phone = Column(String(20))
    segment = Column(String(20), default="new")  # new, regular, loyal, vip
    total_spent = Column(Float, default=0.0)
    cashback_balance = Column(Float, default=0.0)
    total_orders = Column(Integer, default=0)
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)

    orders = relationship("Order", back_populates="client")
    cashback_history = relationship("CashbackHistory", back_populates="client")


class Order(Base):
    """Заказы"""
    __tablename__ = "orders"

    id = Column(Integer, primary_key=True, index=True)
    client_id = Column(Integer, ForeignKey("clients.id"), nullable=False)
    user_id = Column(Integer, ForeignKey("users.id"), nullable=True)
    
    service_name = Column(String(100), nullable=False)
    parameters = Column(Text)  # JSON строка с параметрами
    total_price = Column(Float, nullable=False)
    discount = Column(Float, default=0.0)
    cashback_applied = Column(Float, default=0.0)
    
    status = Column(String(20), default="NEW")  # NEW, PROCESSING, DONE, CANCELLED
    planned_date = Column(DateTime, nullable=True)
    comments = Column(Text, nullable=True)
    
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)

    client = relationship("Client", back_populates="orders")
    user = relationship("User", back_populates="orders")
    cashback_history = relationship("CashbackHistory", back_populates="order")


class Inventory(Base):
    """Складской учет"""
    __tablename__ = "inventory"

    id = Column(Integer, primary_key=True, index=True)
    item_name = Column(String(100), nullable=False)
    item_type = Column(String(50), nullable=False)
    quantity = Column(Float, default=0.0)
    min_quantity = Column(Float, default=0.0)
    unit = Column(String(20), default="шт")
    price_per_unit = Column(Float, nullable=False)
    supplier = Column(String(100), nullable=True)
    notes = Column(Text, nullable=True)
    
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)


class PromoCode(Base):
    """Промокоды"""
    __tablename__ = "promo_codes"

    id = Column(Integer, primary_key=True, index=True)
    code = Column(String(50), unique=True, nullable=False)
    discount_percent = Column(Float, nullable=False)
    max_uses = Column(Integer, default=1)
    current_uses = Column(Integer, default=0)
    is_active = Column(Boolean, default=True)
    valid_until = Column(DateTime, nullable=True)
    created_at = Column(DateTime, default=datetime.utcnow)


class ChatMessage(Base):
    """Сообщения чата (ВКонтакте и внутренние)"""
    __tablename__ = "chat_messages"

    id = Column(Integer, primary_key=True, index=True)
    vk_id = Column(Integer, index=True, nullable=False)
    is_admin = Column(Boolean, default=False)
    message_text = Column(Text, nullable=False)
    timestamp = Column(DateTime, default=datetime.utcnow, index=True)


class CashbackHistory(Base):
    """История операций кэшбэка"""
    __tablename__ = "cashback_history"

    id = Column(Integer, primary_key=True, index=True)
    client_id = Column(Integer, ForeignKey("clients.id"), nullable=False)
    order_id = Column(Integer, ForeignKey("orders.id"), nullable=True)
    operation_type = Column(String(20), nullable=False)  # earned, spent, refunded
    amount = Column(Float, nullable=False)
    description = Column(Text, nullable=True)
    created_at = Column(DateTime, default=datetime.utcnow)

    client = relationship("Client", back_populates="cashback_history")
    order = relationship("Order", back_populates="cashback_history")


class AuditLog(Base):
    """Журнал аудита действий"""
    __tablename__ = "audit_log"

    id = Column(Integer, primary_key=True, index=True)
    user_id = Column(Integer, ForeignKey("users.id"), nullable=True)
    action = Column(String(50), nullable=False)
    entity_type = Column(String(50), nullable=False)
    entity_id = Column(Integer, nullable=False)
    details = Column(Text, nullable=True)
    ip_address = Column(String(45), nullable=True)
    created_at = Column(DateTime, default=datetime.utcnow)

    user = relationship("User", back_populates="audit_logs")


class SystemSettings(Base):
    """
    Глобальные настройки системы.
    Предполагается наличие только одной записи с id=1.
    """
    __tablename__ = "system_settings"

    id = Column(Integer, primary_key=True, default=1)
    is_vacation_mode = Column(Boolean, default=False, nullable=False)
    vacation_end_date = Column(String(50), nullable=True)  # Формат: "DD.MM.YYYY"
    vacation_message = Column(Text, nullable=True)  # Текст автоответа для бота
    
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
