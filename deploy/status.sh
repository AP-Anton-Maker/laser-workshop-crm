#!/bin/bash

# Скрипт не требует sudo для большинства команд, но лучше запускать с ним для systemctl
BLUE='\033[0;34m'
GREEN='\033[0;32m'
NC='\033[0m'

echo -e "${BLUE}=== Статус Laser CRM ===${NC}"
# Проверяем, запущен ли демон
if systemctl is-active --quiet lasercrm; then
    echo -e "Backend (Systemd): ${GREEN}В работе (Active)${NC}"
else
    echo -e "Backend (Systemd): \033[0;31mОстановлен (Inactive)\033[0m"
fi

echo -e "\n${BLUE}=== Последние логи (ошибки) ===${NC}"
journalctl -u lasercrm -n 10 --no-pager | grep -i "error\|warning\|exception" || echo "Ошибок не найдено."

echo -e "\n${BLUE}=== Использование ОЗУ ===${NC}"
free -m

echo -e "\n${BLUE}=== Температура процессора ===${NC}"
# Проверяем утилиту Raspberry Pi (vcgencmd)
if command -v vcgencmd &> /dev/null; then
    vcgencmd measure_temp
# Если это обычный Linux/Ubuntu, читаем напрямую с датчика
elif [ -f /sys/class/thermal/thermal_zone0/temp ]; then
    TEMP=$(cat /sys/class/thermal/thermal_zone0/temp)
    # Перевод миллиградусов в градусы Цельсия
    echo "temp=$((TEMP/1000))'C"
else
    echo "Датчик температуры не найден."
fi
echo -e "${BLUE}========================${NC}"
