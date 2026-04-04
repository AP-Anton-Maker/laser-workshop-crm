from fastapi import APIRouter, Depends, HTTPException, status
from fastapi.security import OAuth2PasswordRequestForm
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select
from datetime import timedelta
from typing import Optional

from ..db.session import get_db
from ..db.models import User
from ..core.security import (
    verify_password, 
    get_password_hash, 
    create_access_token, 
    ACCESS_TOKEN_EXPIRE_MINUTES,
    SECRET_KEY,
    ALGORITHM
)
from fastapi.security import OAuth2PasswordBearer
import jwt

router = APIRouter(prefix="/api/auth", tags=["Authentication"])

oauth2_scheme = OAuth2PasswordBearer(tokenUrl="/api/auth/token")


async def get_current_user(token: str = Depends(oauth2_scheme), db: AsyncSession = Depends(get_db)):
    """
    Зависимость для получения текущего пользователя из токена.
    """
    credentials_exception = HTTPException(
        status_code=status.HTTP_401_UNAUTHORIZED,
        detail="Could not validate credentials",
        headers={"WWW-Authenticate": "Bearer"},
    )
    try:
        payload = jwt.decode(token, SECRET_KEY, algorithms=[ALGORITHM])
        username: str = payload.get("sub")
        if username is None:
            raise credentials_exception
    except jwt.PyJWTError:
        raise credentials_exception
        
    stmt = select(User).where(User.username == username)
    result = await db.execute(stmt)
    user = result.scalars().first()
    
    if user is None:
        raise credentials_exception
    return user


@router.post("/token")
async def login_for_access_token(
    form_data: OAuth2PasswordRequestForm = Depends(),
    db: AsyncSession = Depends(get_db)
):
    """
    Получение JWT токена.
    Принимает username и password (form-data).
    """
    # Поиск пользователя в БД
    stmt = select(User).where(User.username == form_data.username)
    result = await db.execute(stmt)
    user = result.scalars().first()

    # Проверка существования и пароля
    if not user or not verify_password(form_data.password, user.password_hash):
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Неверное имя пользователя или пароль",
            headers={"WWW-Authenticate": "Bearer"},
        )

    # Генерация токена
    access_token_expires = timedelta(minutes=ACCESS_TOKEN_EXPIRE_MINUTES)
    access_token = create_access_token(
        data={"sub": user.username, "role": user.role},
        expires_delta=access_token_expires
    )

    return {"access_token": access_token, "token_type": "bearer"}


# --- Логика инициализации Админа ---

async def create_default_admin(db: AsyncSession):
    """
    Создает пользователя admin/admin, если база пользователей пуста.
    Вызывается при старте приложения.
    """
    stmt = select(User)
    result = await db.execute(stmt)
    users = result.scalars().all()

    if not users:
        print("🔒 Пользователи не найдены. Создание дефолтного администратора...")
        
        admin_password = "admin"
        hashed_pw = get_password_hash(admin_password)
        
        new_admin = User(
            username="admin",
            password_hash=hashed_pw,
            role="admin",
            is_active=True
        )
        
        db.add(new_admin)
        await db.commit()
        print("✅ Администратор создан: login='admin', password='admin'")
    else:
        print(f"✅ База пользователей не пуста ({len(users)} чел.). Пропускаем создание админа.")
