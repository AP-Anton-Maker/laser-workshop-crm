#!/bin/bash

# ⏹️ Laser CRM - Остановка сервисов

echo "⏹️ Остановка Laser CRM..."

# Остановка backend сервиса
echo "🛑 Остановка backend (uvicorn)..."
sudo systemctl stop lasercrm
if [ $? -eq 0 ]; then
    echo "✅ Backend остановлен."
else
    echo "⚠️ Не удалось остановить backend."
fi

# Остановка web сервера
echo "🛑 Остановка web server (nginx)..."
sudo systemctl stop nginx
if [ $? -eq 0 ]; then
    echo "✅ Nginx остановлен."
else
    echo "⚠️ Не удалось остановить nginx."
fi

echo "--------------------------"
echo "⏸️  Система остановлена."
echo "💡 Для запуска используйте: ./start.sh"
