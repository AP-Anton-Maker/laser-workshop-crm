#!/bin/bash
# Скрипт резервного копирования базы данных и медиа-файлов
# Запускается ежедневно через CRON

set -e

# Настройки
PROJECT_DIR="/opt/anton-maker"
BACKUP_DIR="/var/backups/anton-maker"
DATE=$(date +%Y%m%d_%H%M%S)
RETENTION_DAYS=30

# Создаем директорию для бэкапов
mkdir -p "$BACKUP_DIR"

echo "[$(date)] Начало резервного копирования..."

# 1. Бэкап базы данных SQLite с WAL
echo "[$(date)] Копирование базы данных..."
cp "$PROJECT_DIR/data/db.sqlite3" "$BACKUP_DIR/db_$DATE.sqlite3"

# Копируем WAL файлы если существуют
if [ -f "$PROJECT_DIR/data/db.sqlite3-wal" ]; then
    cp "$PROJECT_DIR/data/db.sqlite3-wal" "$BACKUP_DIR/db_$DATE.sqlite3-wal"
fi
if [ -f "$PROJECT_DIR/data/db.sqlite3-shm" ]; then
    cp "$PROJECT_DIR/data/db.sqlite3-shm" "$BACKUP_DIR/db_$DATE.sqlite3-shm"
fi

# 2. Архивация медиа-файлов
echo "[$(date)] Архивация медиа-файлов..."
tar -czf "$BACKUP_DIR/media_$DATE.tar.gz" -C "$PROJECT_DIR/data" media/

# 3. Архивация конфигов
echo "[$(date)] Архивация конфигурационных файлов..."
tar -czf "$BACKUP_DIR/config_$DATE.tar.gz" -C "$PROJECT_DIR" .env requirements.txt deploy/

# 4. Сжатие бэкапа БД
echo "[$(date)] Сжатие базы данных..."
gzip -f "$BACKUP_DIR/db_$DATE.sqlite3"
if [ -f "$BACKUP_DIR/db_$DATE.sqlite3-wal" ]; then
    gzip -f "$BACKUP_DIR/db_$DATE.sqlite3-wal"
fi
if [ -f "$BACKUP_DIR/db_$DATE.sqlite3-shm" ]; then
    gzip -f "$BACKUP_DIR/db_$DATE.sqlite3-shm"
fi

# 5. Удаление старых бэкапов
echo "[$(date)] Очистка старых бэкапов (старше $RETENTION_DAYS дней)..."
find "$BACKUP_DIR" -name "*.sqlite3.gz" -mtime +$RETENTION_DAYS -delete
find "$BACKUP_DIR" -name "*.tar.gz" -mtime +$RETENTION_DAYS -delete

# 6. Вывод информации о размере бэкапа
BACKUP_SIZE=$(du -sh "$BACKUP_DIR" | cut -f1)
echo "[$(date)] Размер директории бэкапов: $BACKUP_SIZE"

# 7. Список последних бэкапов
echo "[$(date)] Последние 5 бэкапов:"
ls -lht "$BACKUP_DIR" | head -6

echo "[$(date)] Резервное копирование завершено успешно!"
