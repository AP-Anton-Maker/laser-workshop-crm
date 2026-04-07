#!/bin/bash

BLUE='\033[0;34m'
GREEN='\033[0;32m'
RED='\033[0;31m'
NC='\033[0m'

echo -e "${BLUE}=== Статус Laser CRM ===${NC}"
# Проверяем, запущен ли демон
if systemctl is-active --quiet lasercrm; then
    echo -e "Backend (Systemd): ${GREEN}В работе (Active)${NC}"
else
    echo -e "Backend (Systemd): ${RED}Остановлен (Inactive)${NC}"
fi

echo -e "\n${BLUE}=== Последние логи (ошибки) ===${NC}"
journalctl -u lasercrm -n 10 --no-pager | grep -i "error\|warning\|exception" || echo "Ошибок не найдено."

echo -e "\n${BLUE}=== Использование ОЗУ ===${NC}"
free -m

echo -e "\n${BLUE}=== Температура процессора ===${NC}"
if command -v vcgencmd &> /dev/null; then
    vcgencmd measure_temp
elif [ -f /sys/class/thermal/thermal_zone0/temp ]; then
    TEMP=$(cat /sys/class/thermal/thermal_zone0/temp)
    echo "temp=$((TEMP/1000))'C"
else
    echo "Датчик температуры не найден."
fi
echo -e "${BLUE}========================${NC}"
