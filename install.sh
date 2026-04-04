#!/bin/bash

# 🔧 Laser CRM - Автоматический установщик (DevOps Edition)
# Запускать от имени пользователя с правами sudo (но не под root)

set -e

echo "🚀 Начало установки Laser CRM..."

# 1. Определение переменных окружения
PROJECT_DIR=$(pwd)
USER_NAME=$(whoami)
BACKEND_DIR="$PROJECT_DIR/backend"
FRONTEND_DIR="$PROJECT_DIR/frontend"
VENV_DIR="$BACKEND_DIR/venv"

echo "📂 Проект расположен в: $PROJECT_DIR"
echo "👤 Пользователь: $USER_NAME"

# Проверка прав sudo
if [ "$EUID" -eq 0 ]; then 
  echo "❌ Пожалуйста, не запускайте этот скрипт от root. Запустите как обычный пользователь (скрипт сам запросит sudo)."
  exit 1
fi

# 2. Установка системных зависимостей
echo "📦 Установка системных пакетов..."
sudo apt update
sudo apt install -y python3-venv python3-dev nginx ufw git

# 3. Настройка Python окружения
echo "🐍 Создание виртуального окружения..."
if [ ! -d "$VENV_DIR" ]; then
    python3 -m venv "$VENV_DIR"
else
    echo "⚠️ Виртуальное окружение уже существует, пропускаем создание."
fi

echo "⬇️ Установка Python зависимостей..."
source "$VENV_DIR/bin/activate"
pip install --upgrade pip
pip install -r "$BACKEND_DIR/requirements.txt"
deactivate

# 4. Генерация файла .env если его нет
if [ ! -f "$BACKEND_DIR/.env" ]; then
    echo "⚙️ Создание файла .env..."
    cat > "$BACKEND_DIR/.env" <<EOF
VK_TOKEN=ваш_токен_группы
SECRET_KEY=super_secret_key_change_me_$(openssl rand -hex 16)
DATABASE_URL=sqlite+aiosqlite:///../data/laser_crm.sqlite3
EOF
    echo "⚠️ ВНИМАНИЕ: Не забудьте отредактировать $BACKEND_DIR/.env и указать реальный VK_TOKEN!"
fi

# 5. Настройка Systemd
echo "🔧 Настройка сервиса Systemd..."
sudo tee /etc/systemd/system/lasercrm.service > /dev/null <<EOF
[Unit]
Description=Laser CRM Application
After=network.target

[Service]
User=$USER_NAME
Group=$USER_NAME
WorkingDirectory=$BACKEND_DIR
Environment="PATH=$VENV_DIR/bin"
ExecStart=$VENV_DIR/bin/uvicorn main:app --host 127.0.0.1 --port 8000
Restart=always
RestartSec=10

[Install]
WantedBy=multi-user.target
EOF

# 6. Настройка Nginx
echo "🌐 Настройка Nginx..."
sudo rm -f /etc/nginx/sites-available/default
sudo tee /etc/nginx/sites-available/lasercrm > /dev/null <<EOF
server {
    listen 80;
    server_name _;

    # Раздача статики (Frontend)
    location / {
        root $FRONTEND_DIR;
        index index.html;
        try_files \$uri \$uri/ /index.html;
    }

    # Проксирование API запросов на Backend
    location /api/ {
        proxy_pass http://127.0.0.1:8000;
        proxy_set_header Host \$host;
        proxy_set_header X-Real-IP \$remote_addr;
        proxy_set_header X-Forwarded-For \$proxy_add_x_forwarded_for;
        proxy_set_header X-Forwarded-Proto \$scheme;
    }
}
EOF

# Активация конфига Nginx
sudo ln -sf /etc/nginx/sites-available/lasercrm /etc/nginx/sites-enabled/lasercrm
sudo nginx -t

# 7. Настройка Firewall (UFW)
echo "🔒 Настройка брандмауэра UFW..."
sudo ufw allow OpenSSH
sudo ufw allow 'Nginx HTTP'
echo "y" | sudo ufw enable || true # 'y' для автоматического подтверждения, || true чтобы не падать если уже включен

# 8. Запуск служб
echo "▶️ Запуск служб..."
sudo systemctl daemon-reload
sudo systemctl enable lasercrm
sudo systemctl start lasercrm
sudo systemctl enable nginx
sudo systemctl restart nginx

# Финальное сообщение
echo ""
echo "✅ Установка завершена успешно!"
echo "--------------------------------"
echo "🌐 Приложение доступно по адресу: http://$(hostname -I | awk '{print $1}')"
echo "📄 Логи приложения: sudo journalctl -u lasercrm -f"
echo "⚙️  Конфиг сервиса: /etc/systemd/system/lasercrm.service"
echo ""
echo "🔑 Дефолтные доступы: admin / admin"
echo "Не забудьте проверить файл $BACKEND_DIR/.env!"
