from datetime import datetime, timedelta
from typing import Optional
from jose import jwt # Или используйте стандартный jwt, если установлен PyJWT
from passlib.context import CryptContext
from ..core.config import settings

# Настройки безопасности
# В продакшене SECRET_KEY нужно брать из переменных окружения!
SECRET_KEY = settings.SECRET_KEY if hasattr(settings, 'SECRET_KEY') else "super-secret-key-change-me-in-production"
ALGORITHM = "HS256"
ACCESS_TOKEN_EXPIRE_MINUTES = 3000  # Время жизни токена (минуты)

# Контекст для хеширования паролей (bcrypt)
pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto")


def verify_password(plain_password: str, hashed_password: str) -> bool:
    """
    Проверяет соответствие открытого пароля его хешу.
    """
    return pwd_context.verify(plain_password, hashed_password)


def get_password_hash(password: str) -> str:
    """
    Генерирует хеш пароля используя bcrypt.
    """
    return pwd_context.hash(password)


def create_access_token(data: dict, expires_delta: Optional[timedelta] = None) -> str:
    """
    Создает JWT токен.
    :param data: Данные для кодирования (обычно {"sub": username})
    :param expires_delta: Время жизни токена
    :return: Строка токена
    """
    to_encode = data.copy()
    
    if expires_delta:
        expire = datetime.utcnow() + expires_delta
    else:
        expire = datetime.utcnow() + timedelta(minutes=ACCESS_TOKEN_EXPIRE_MINUTES)
        
    to_encode.update({"exp": expire})
    
    encoded_jwt = jwt.encode(to_encode, SECRET_KEY, algorithm=ALGORITHM)
    return encoded_jwt
