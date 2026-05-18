#!/bin/bash
# Anton Maker CRM - Автоматическая установка на Debian 12 LXC
# Запуск: bash deploy/install.sh

set -e

echo "🚀 Anton Maker CRM - Установка"
echo "=============================="

# Цвета для вывода
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
NC='\033[0m' # No Color

# Проверка прав root
if [ "$EUID" -ne 0 ]; then 
    echo -e "${RED}Ошибка: Запустите скрипт от root${NC}"
    exit 1
fi

# Переменные
PROJECT_DIR="/opt/anton-maker"
VENV_DIR="${PROJECT_DIR}/venv"
DATA_DIR="${PROJECT_DIR}/data"
STATIC_DIR="${DATA_DIR}/static"
MEDIA_DIR="${DATA_DIR}/media"
SERVICE_NAME="anton-maker"
NGINX_CONF="/etc/nginx/sites-available/anton-maker"

echo -e "${GREEN}[1/8] Обновление пакетов...${NC}"
apt-get update -qq
apt-get upgrade -y -qq

echo -e "${GREEN}[2/8] Установка системных зависимостей...${NC}"
apt-get install -y -qq \
    python3.11 \
    python3.11-venv \
    python3-pip \
    nginx \
    libcairo2 \
    libpango-1.0-0 \
    libpangocairo-1.0-0 \
    libgdk-pixbuf2.0-0 \
    shared-mime-info \
    libffi-dev \
    pkg-config \
    build-essential

echo -e "${GREEN}[3/8] Создание виртуального окружения...${NC}"
cd ${PROJECT_DIR}
python3.11 -m venv ${VENV_DIR}
source ${VENV_DIR}/bin/activate

echo -e "${GREEN}[4/8] Установка Python зависимостей...${NC}"
pip install --upgrade pip -q
pip install -r requirements.txt -q

echo -e "${GREEN}[5/8] Создание директорий...${NC}"
mkdir -p ${DATA_DIR} ${STATIC_DIR} ${MEDIA_DIR}
touch ${DATA_DIR}/.gitkeep

echo -e "${GREEN}[6/8] Настройка .env файла...${NC}"
if [ ! -f "${PROJECT_DIR}/.env" ]; then
    cp .env.example .env
    echo -e "${YELLOW}⚠️  Не забудьте настроить .env файл!${NC}"
    echo "   Отредактируйте: nano ${PROJECT_DIR}/.env"
fi

echo -e "${GREEN}[7/8] Инициализация базы данных...${NC}"
python manage.py migrate --noinput
python manage.py collectstatic --noinput

# Создание суперпользователя по умолчанию
echo "from django.contrib.auth import get_user_model; User = get_user_model(); User.objects.filter(username='admin').exists() or User.objects.create_superuser('admin', 'admin@anton-maker.ru', 'admin123')" | python manage.py shell
echo -e "${YELLOW}👤 Суперпользователь создан: admin / admin123${NC}"

echo -e "${GREEN}[8/8] Настройка systemd и nginx...${NC}"

# Systemd service
cat > /etc/systemd/system/${SERVICE_NAME}.service << EOF
[Unit]
Description=Anton Maker CRM Gunicorn service
After=network.target

[Service]
User=root
Group=root
WorkingDirectory=${PROJECT_DIR}
ExecStart=${VENV_DIR}/bin/gunicorn --workers 2 --threads 4 --bind unix:${PROJECT_DIR}/gunicorn.sock config.wsgi:application
Restart=always
RestartSec=5

[Install]
WantedBy=multi-user.target
EOF

systemctl daemon-reload
systemctl enable ${SERVICE_NAME}
systemctl start ${SERVICE_NAME}

# Nginx configuration
cat > ${NGINX_CONF} << EOF
server {
    listen 80;
    server_name anton-maker.ru www.anton-maker.ru;
    
    location = /favicon.ico { access_log off; log_not_found off; }
    
    location /static/ {
        alias ${STATIC_DIR}/;
    }
    
    location /media/ {
        alias ${MEDIA_DIR}/;
    }
    
    location / {
        include proxy_params;
        proxy_pass http://unix:${PROJECT_DIR}/gunicorn.sock;
        proxy_set_header Host \$host;
        proxy_set_header X-Real-IP \$remote_addr;
        proxy_set_header X-Forwarded-For \$proxy_add_x_forwarded_for;
        proxy_set_header X-Forwarded-Proto \$scheme;
    }
}
EOF

ln -sf ${NGINX_CONF} /etc/nginx/sites-enabled/
nginx -t
systemctl restart nginx

echo ""
echo -e "${GREEN}✅ Установка завершена!${NC}"
echo ""
echo "📊 Статус сервиса:"
systemctl status ${SERVICE_NAME} --no-pager
echo ""
echo "🌐 Сайт доступен: http://anton-maker.ru"
echo "🔧 Админка: http://anton-maker.ru/admin/"
echo "🧮 Калькулятор: http://anton-maker.ru/calculator/"
echo "🔗 VK Webhook: http://anton-maker.ru/webhook/"
echo ""
echo -e "${YELLOW}⚠️  Следующие шаги:${NC}"
echo "1. Отредактируйте .env файл с вашими настройками"
echo "2. Настройте SSL через certbot (опционально)"
echo "3. Настройте VK webhook в панели разработчика VK"
echo ""
echo "📋 Полезные команды:"
echo "   systemctl status anton-maker  - статус сервиса"
echo "   journalctl -u anton-maker -f  - логи"
echo "   systemctl restart anton-maker - перезапуск"
