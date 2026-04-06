from typing import List
from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.future import select

from db.session import get_db
from db.models import Client, User
from schemas import ClientCreate, ClientUpdate, ClientResponse
from api.deps import get_current_active_user

router = APIRouter(prefix="/clients", tags=["Клиенты"])

@router.post("/", response_model=ClientResponse, status_code=status.HTTP_201_CREATED)
async def create_client(
    client_in: ClientCreate,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_active_user)
):
    """Создает нового клиента."""
    if client_in.vk_id:
        stmt = select(Client).where(Client.vk_id == client_in.vk_id)
        result = await db.execute(stmt)
        if result.scalar_one_or_none():
            raise HTTPException(status_code=400, detail="Клиент с таким VK ID уже существует.")

    new_client = Client(
        name=client_in.name,
        vk_id=client_in.vk_id,
        phone=client_in.phone,
        notes=client_in.notes
    )
    db.add(new_client)
    await db.commit()
    await db.refresh(new_client)
    return new_client

@router.get("/", response_model=List[ClientResponse])
async def read_clients(
    skip: int = 0,
    limit: int = 100,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_active_user)
):
    """Возвращает список всех клиентов."""
    stmt = select(Client).offset(skip).limit(limit).order_by(Client.id.desc())
    result = await db.execute(stmt)
    return result.scalars().all()

@router.get("/{client_id}", response_model=ClientResponse)
async def read_client(
    client_id: int,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_active_user)
):
    """Получает данные одного клиента по ID."""
    client = await db.get(Client, client_id)
    if not client:
        raise HTTPException(status_code=404, detail="Клиент не найден")
    return client

@router.put("/{client_id}", response_model=ClientResponse)
async def update_client(
    client_id: int,
    client_in: ClientUpdate,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_active_user)
):
    """Обновляет данные клиента."""
    client = await db.get(Client, client_id)
    if not client:
        raise HTTPException(status_code=404, detail="Клиент не найден")

    update_data = client_in.model_dump(exclude_unset=True)
    for field, value in update_data.items():
        setattr(client, field, value)

    await db.commit()
    await db.refresh(client)
    return client

@router.delete("/{client_id}", status_code=status.HTTP_204_NO_CONTENT)
async def delete_client(
    client_id: int,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_active_user)
):
    """Удаляет клиента из базы данных."""
    client = await db.get(Client, client_id)
    if not client:
        raise HTTPException(status_code=404, detail="Клиент не найден")
        
    await db.delete(client)
    await db.commit()
