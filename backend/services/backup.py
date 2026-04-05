import os
import csv
import zipfile
from datetime import datetime
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select

from db.models import Client, Order

class BackupService:
    @staticmethod
    async def create_full_backup(db: AsyncSession) -> str:
        """
        Создает ZIP-архив с CSV-экспортом клиентов, заказов и копией базы данных.
        Возвращает абсолютный путь к созданному ZIP-файлу.
        """
        # Создаем папку для временных файлов бэкапа
        backup_dir = os.path.join(os.getcwd(), "temp_backups")
        os.makedirs(backup_dir, exist_ok=True)
        
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        zip_filename = os.path.join(backup_dir, f"laser_crm_backup_{timestamp}.zip")
        clients_csv = os.path.join(backup_dir, "clients.csv")
        orders_csv = os.path.join(backup_dir, "orders.csv")
        
        # 1. Экспорт Клиентов в CSV
        clients_res = await db.execute(select(Client))
        clients = clients_res.scalars().all()
        with open(clients_csv, "w", newline="", encoding="utf-8") as f:
            writer = csv.writer(f)
            writer.writerow(["ID", "Имя", "VK ID", "Телефон", "Email", "Заметки", "Дата регистрации"])
            for c in clients:
                writer.writerow([c.id, c.name, c.vk_id, c.phone, c.email, c.notes, c.created_at])
                
        # 2. Экспорт Заказов в CSV
        orders_res = await db.execute(select(Order))
        orders = orders_res.scalars().all()
        with open(orders_csv, "w", newline="", encoding="utf-8") as f:
            writer = csv.writer(f)
            writer.writerow(["ID", "ID Клиента", "Описание", "Статус", "Цена", "Себестоимость", "Создан", "Дедлайн"])
            for o in orders:
                writer.writerow([o.id, o.client_id, o.description, o.status, o.price, o.cost_price, o.created_at, o.deadline])
                
        # 3. Упаковываем всё в ZIP (вместе с самим файлом базы SQLite, если он есть)
        db_path = os.path.join(os.path.dirname(os.getcwd()), "data", "laser_crm.sqlite3")
        
        with zipfile.ZipFile(zip_filename, "w", zipfile.ZIP_DEFLATED) as zipf:
            zipf.write(clients_csv, arcname="clients_export.csv")
            zipf.write(orders_csv, arcname="orders_export.csv")
            if os.path.exists(db_path):
                zipf.write(db_path, arcname="database.sqlite3")
                
        # Очищаем временные CSV файлы
        os.remove(clients_csv)
        os.remove(orders_csv)
        
        return zip_filename
