"""
Модели базы данных для Laser CRM.
Flat-архитектура: параметры заказов хранятся в текстовом виде (Требование 3.3).

Модели основаны на полях из index.html и ТЗ (Части 3, 5, 6):
- User: Пользователи системы (admin, manager, master)
- Order: Заказы с параметрами в текстовом формате
- Client: Клиенты с сегментацией и кэшбеком
- Inventory: Складской учёт материалов
- PromoCode: Промокоды со скидками
"""
from datetime import datetime
from sqlalchemy import Column, Integer, String, Float, DateTime, ForeignKey, Text, Boolean
from sqlalchemy.orm import relationship

from db.session import Base


class User(Base):
    """
    Модель пользователя системы.
    Роли: admin, manager, master
    """
    __tablename__ = "users"
    
    id = Column(Integer, primary_key=True, index=True)
    username = Column(String(50), unique=True, index=True, nullable=False)
    password_hash = Column(String(255), nullable=False)
    role = Column(String(20), nullable=False, default="manager")  # admin, manager, master
    created_at = Column(DateTime, default=datetime.utcnow)
    is_active = Column(Boolean, default=True)
    
    # Связи
    orders = relationship("Order", back_populates="manager")
    audit_logs = relationship("AuditLog", back_populates="user")
    
    def __repr__(self):
        return f"<User(id={self.id}, username='{self.username}', role='{self.role}')>"


class Client(Base):
    """
    Модель клиента с поддержкой LTV и кэшбэка
    """
    __tablename__ = "clients"

    id = Column(Integer, primary_key=True, index=True)
    name = Column(String(100), nullable=False)
    vk_id = Column(String(50), index=True)  # ID в VK (может быть строкой или числом)
    phone = Column(String(20))
    
    # Сегментация и статистика
    customer_segment = Column(String(20), default="new")  # new, regular, loyal, vip
    total_orders = Column(Integer, default=0)
    total_spent = Column(Float, default=0.0)  # LTV (Life Time Value)
    cashback_balance = Column(Float, default=0.0)  # Доступные баллы
    cashback_earned_total = Column(Float, default=0.0)  # Всего заработано за все время
    
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)

    # Связи
    orders = relationship("Order", back_populates="client", cascade="all, delete-orphan")
    cashback_history = relationship("CashbackHistory", back_populates="client", cascade="all, delete-orphan")

class Order(Base):
    """
    Обновленная модель заказа (добавлена связь с cashback_history)
    """
    __tablename__ = "orders"

    id = Column(Integer, primary_key=True, index=True)
    client_id = Column(Integer, ForeignKey("clients.id"), nullable=False)
    user_id = Column(Integer, ForeignKey("users.id"), nullable=True)
    
    service_name = Column(String(100), nullable=False)
    parameters = Column(Text)  # JSON строка
    total_price = Column(Float, nullable=False)
    discount = Column(Float, default=0.0)
    cashback_applied = Column(Float, default=0.0)
    
    status = Column(String(20), default="NEW")  # NEW, PROCESSING, DONE, CANCELLED
    planned_date = Column(DateTime, nullable=True)
    comments = Column(Text, nullable=True)
    
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)

    # Связи
    client = relationship("Client", back_populates="orders")
    user = relationship("User", back_populates="orders", foreign_keys=[user_id])
    cashback_history = relationship("CashbackHistory", back_populates="order", cascade="all, delete-orphan")

# ... остальные модели (User, Inventory, PromoCode, ChatMessage, AuditLog) остаются без изменений ...

class Inventory(Base):
    """
    Модель складского учёта.
    Типы: material, product, consumable (Требование 6)
    """
    __tablename__ = "inventory"
    
    id = Column(Integer, primary_key=True, index=True)
    item_name = Column(String(100), nullable=False)  # Наименование товара
    item_type = Column(String(20), nullable=False)  # material, product, consumable
    quantity = Column(Float, default=0.0)  # Текущий остаток
    min_quantity = Column(Float, default=0.0)  # Минимальный остаток для уведомления
    unit = Column(String(20), default="шт")  # Единица измерения (шт, м, см², кг)
    price_per_unit = Column(Float, default=0.0)  # Цена за единицу
    supplier = Column(String(100), nullable=True)  # Поставщик (Требование 6.8)
    notes = Column(Text, nullable=True)  # Комментарий
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    
    def __repr__(self):
        return f"<Inventory(id={self.id}, name='{self.item_name}', quantity={self.quantity})>"


class PromoCode(Base):
    """
    Модель промокодов.
    Система промокодов со скидками (Требование 5.2)
    """
    __tablename__ = "promo_codes"
    
    id = Column(Integer, primary_key=True, index=True)
    code = Column(String(50), unique=True, index=True, nullable=False)  # Код промокода
    discount_percent = Column(Float, nullable=False)  # Процент скидки
    max_uses = Column(Integer, default=100)  # Максимальное количество использований
    current_uses = Column(Integer, default=0)  # Текущее количество использований
    is_active = Column(Boolean, default=True)  # Активен ли промокод
    valid_until = Column(DateTime, nullable=True)  # Срок действия
    created_at = Column(DateTime, default=datetime.utcnow)
    
    def __repr__(self):
        return f"<PromoCode(code='{self.code}', discount={self.discount_percent}%)>"


class CashbackHistory(Base):
    """
    История операций кэшбэка (начисления и списания)
    """
    __tablename__ = "cashback_history"

    id = Column(Integer, primary_key=True, index=True)
    client_id = Column(Integer, ForeignKey("clients.id"), nullable=False)
    order_id = Column(Integer, ForeignKey("orders.id"), nullable=True)  # Связь с заказом (если начисление за заказ)
    
    operation_type = Column(String(20), nullable=False)  # 'earned' (начислено), 'spent' (списано), 'refunded' (возврат)
    amount = Column(Float, nullable=False)  # Сумма операции (всегда положительная, тип операции указывает направление)
    description = Column(Text, nullable=True)  # Комментарий (например, "За заказ #123")
    
    created_at = Column(DateTime, default=datetime.utcnow, index=True)

    # Связи
    client = relationship("Client", back_populates="cashback_history")
    order = relationship("Order", back_populates="cashback_history")

class AuditLog(Base):
    """
    Журнал аудита действий пользователей.
    Логирование всех действий администратора (Требование 8.5)
    """
    __tablename__ = "audit_log"
    
    id = Column(Integer, primary_key=True, index=True)
    user_id = Column(Integer, ForeignKey("users.id"), nullable=True)
    action = Column(String(255), nullable=False)  # Описание действия
    entity_type = Column(String(50), nullable=True)  # Тип сущности (order, client, etc.)
    entity_id = Column(Integer, nullable=True)  # ID сущности
    details = Column(Text, nullable=True)  # Дополнительные детали (JSON)
    ip_address = Column(String(45), nullable=True)  # IP адрес
    created_at = Column(DateTime, default=datetime.utcnow, index=True)

class ChatMessage(Base):
    """
    Модель сообщений чата с клиентами ВКонтакте
    """
    __tablename__ = "chat_messages"

    id = Column(Integer, primary_key=True, index=True)
    vk_id = Column(Integer, index=True, nullable=False)  # ID пользователя ВК
    is_admin = Column(Boolean, default=False, nullable=False)  # False = клиент, True = админ/менеджер
    message_text = Column(Text, nullable=False)  # Текст сообщения
    timestamp = Column(DateTime, default=datetime.utcnow, index=True)  # Время отправки
    
    # Связи можно добавить позже, если нужно связывать с Client по vk_id
    
    # Связи
    user = relationship("User", back_populates="audit_logs")
    
    def __repr__(self):
        return f"<AuditLog(id={self.id}, action='{self.action}', user_id={self.user_id})>"
