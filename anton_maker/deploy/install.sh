#!/bin/bash
set -e

echo "🚀 Установка Anton Maker CRM..."

# Обновление системы
apt update
apt install -y python3-venv python3-pip nginx libpango-1.0-0 libharfbuzz0b libffi-dev libjpeg-dev zlib1g-dev

# Создание виртуального окружения
cd /opt/anton_maker
python3 -m venv venv
source venv/bin/activate

# Установка зависимостей Python
pip install --upgrade pip
pip install -r requirements.txt

# Создание директорий
mkdir -p /run/anton
mkdir -p data/media data/static

# Настройка прав
chown -R www-data:www-data /opt/anton_maker/data
chmod -R 755 /opt/anton_maker/data

# Применение миграций
python manage.py migrate

# Сбор статики
python manage.py collectstatic --noinput

# Создание суперпользователя (интерактивно)
echo ""
echo "👤 Создайте суперпользователя:"
python manage.py createsuperuser

# Копирование конфигов
cp deploy/anton-maker.service /etc/systemd/system/
cp deploy/nginx.conf /etc/nginx/sites-available/anton-maker
ln -sf /etc/nginx/sites-available/anton-maker /etc/nginx/sites-enabled/
rm -f /etc/nginx/sites-enabled/default

# Перезапуск сервисов
systemctl daemon-reload
systemctl enable anton-maker
systemctl start anton-maker
systemctl restart nginx

echo ""
echo "✅ Установка завершена!"
echo "📝 Админка: https://ваш-домен.ru/secret-admin/"
echo "🤖 Webhook: https://ваш-домен.ru/bot/webhook/"
echo ""
echo "Не забудьте:"
echo "1. Настроить .env файл"
echo "2. Получить SSL сертификат через certbot"
echo "3. Настроить webhook ВКонтакте"
