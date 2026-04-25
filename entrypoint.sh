#!/bin/bash

# Применяем изменения в базе данных
python manage.py migrate --noinput

# Собираем статические файлы для админки и Caddy
python manage.py collectstatic --noinput

# Запускаем WEB-сервер (Gunicorn) на переднем плане
exec gunicorn config.wsgi --workers 2 --threads 4 -b 0.0.0.0:8000
