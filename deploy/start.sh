#!/bin/bash

# Цвета
GREEN='\033[0;32m'
NC='\033[0m'
RED='\033[0;31m'

if [ "$EUID" -ne 0 ]; then
  echo -e "${RED}Пожалуйста, запустите через sudo: sudo ./deploy/start.sh${NC}"
  exit 1
fi

echo "Перезапуск Laser CRM и Nginx..."

# Перезапуск бэкенда
systemctl restart lasercrm

# Перезапуск веб-сервера
systemctl restart nginx

echo -e "${GREEN}Сервисы успешно перезапущены!${NC}"
