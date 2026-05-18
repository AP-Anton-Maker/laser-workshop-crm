#!/bin/sh
set -e

# Ожидание готовности БД (если будет PostgreSQL в будущем)
# Миграции ТОЛЬКО если это основной реплик
if [ "$RUN_MIGRATIONS" = "1" ]; then
  python manage.py migrate --noinput
fi

# Сбор статиков
python manage.py collectstatic --noinput --clear

# Запуск Gunicorn: 2 worker × 4 threads = оптимально для 4 ядер N100
exec gunicorn config.wsgi:application \
  --workers 2 \
  --threads 4 \
  --worker-class gthread \
  --timeout 120 \
  --bind 0.0.0.0:8000 \
  --access-logfile - \
  --error-logfile -
