#!/bin/bash

# Применяем изменения в базе данных
python manage.py migrate --noinput

# Собираем красивые стили для админки Unfold
python manage.py collectstatic --noinput

# Запускаем WEB-сервер админки в фоновом режиме (на 2 рабочих процесса, бережем ОЗУ)
gunicorn config.wsgi:application --bind 0.0.0.0:8000 --workers 2 &

# Запускаем нашего бота ВК на переднем плане
python manage.py run_bot
