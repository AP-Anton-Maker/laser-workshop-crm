#!/bin/bash
# deploy/backup.sh

set -e

PROJECT_DIR="/opt/anton_maker"
DB_PATH="$PROJECT_DIR/data/db.sqlite3"
BACKUP_DIR="$PROJECT_DIR/backups"
RETENTION_DAYS=30
DATE_STAMP=$(date +%Y%m%d_%H%M%S)
BACKUP_FILE="$BACKUP_DIR/db_backup_$DATE_STAMP.sqlite3"

# Создание директории бэкапов
mkdir -p "$BACKUP_DIR"

echo "[$(date '+%Y-%m-%d %H:%M:%S')] Начало бэкапа..."

# Проверка существования БД
if [ ! -f "$DB_PATH" ]; then
    echo "Ошибка: Файл базы данных не найден в $DB_PATH"
    exit 1
fi

# Создание бэкапа через sqlite3 (безопасно для WAL)
sqlite3 "$DB_PATH" ".backup '$BACKUP_FILE'"

# Сжатие
gzip "$BACKUP_FILE"
echo "Создан архив: ${BACKUP_FILE}.gz"

# Удаление старых бэкапов
echo "Удаление бэкапов старше $RETENTION_DAYS дней..."
find "$BACKUP_DIR" -name "db_backup_*.sqlite3.gz" -type f -mtime +$RETENTION_DAYS -delete

echo "[$(date '+%Y-%m-%d %H:%M:%S')] Бэкап успешно завершен."
