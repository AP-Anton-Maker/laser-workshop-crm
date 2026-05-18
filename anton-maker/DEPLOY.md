# Деплой Anton Maker CRM на Proxmox LXC (Debian 12)

Данный документ описывает процесс установки и настройки системы Anton Maker CRM на контейнер Proxmox LXC с Debian 12.

## 📋 Требования к системе

- **ОС**: Debian 12 (в Proxmox LXC)
- **Ресурсы**: Минимум 4 ядра CPU, 4 ГБ RAM, 30 ГБ SSD
- **Сеть**: Постоянный IP-адрес, доступ к портам 80/443
- **Опции LXC**: Включить `Nesting=1` для совместимости

## 🚀 Быстрая установка

### Шаг 1: Подготовка контейнера

1. Создайте контейнер в Proxmox:
   - Шаблон: `debian-12-standard`
   - CPU: 4 ядра
   - RAM: 4096 MB
   - Диск: 30 GB
   - **Обязательно** включите `Features → Nesting=1`

2. Подключитесь к консоли контейнера и обновите систему:
```bash
apt update && apt upgrade -y
```

### Шаг 2: Установка проекта

1. Установите Git и клонируйте репозиторий:
```bash
apt install -y git
cd /opt
git clone https://github.com/your-username/anton-maker.git
cd anton-maker
```

2. Настройте переменные окружения:
```bash
cp .env.example .env
nano .env
```
Заполните обязательные поля:
- `SECRET_KEY` (сгенерируйте случайный ключ)
- `VK_APP_ID` (ID приложения ВКонтакте)
- `VK_TOKEN` (сервисный токен сообщества)
- `VK_CONFIRMATION_CODE` (код подтверждения вебхука)
- `ADMIN_VK_ID` (ваш ID ВКонтакте)
- `ALLOWED_HOSTS` (ваш домен, например: `anton-maker.ru,www.anton-maker.ru`)

### Шаг 3: Запуск установки

Выполните скрипт автоматической установки:
```bash
bash deploy/install.sh
```

Скрипт выполнит:
- Установку системных зависимостей (Python, pip, nginx, certbot)
- Создание виртуального окружения Python
- Установку Python-пакетов из `requirements.txt`
- Миграцию базы данных
- Сборку статических файлов
- Настройку Gunicorn и Nginx
- Создание systemd-сервиса
- Запуск приложения

### Шаг 4: Настройка домена и SSL

1. В панели управления вашего DNS-хостинга:
   - Добавьте A-запись: `anton-maker.ru` → IP-адрес вашего контейнера
   - Добавьте CNAME-запись: `www.anton-maker.ru` → `anton-maker.ru`

2. После того как DNS-записи применятся (до 24 часов), настройте SSL:
```bash
# Установите Certbot если ещё не установлен
apt install -y certbot python3-certbot-nginx

# Получите SSL-сертификат
certbot --nginx -d anton-maker.ru -d www.anton-maker.ru
```

3. Отредактируйте конфигурацию Nginx, раскомментировав HTTPS-блок:
```bash
nano /etc/nginx/sites-available/anton-maker
```
Раскомментируйте весь блок `# HTTPS server` и убедитесь, что HTTP-сервер перенаправляет на HTTPS.

4. Перезапустите Nginx:
```bash
systemctl reload nginx
```

### Шаг 5: Настройка ВКонтакте

1. Зайдите в [Кабинет сообщества](https://vk.com/groups) ВКонтакте
2. Перейдите в раздел "Управление" → "Работа с API" → "Long Poll API"
3. Включите Long Poll API и выберите тип "Веб-хуки"
4. Укажите адрес вебхука: `https://anton-maker.ru/webhook/`
5. Введите код подтверждения из `.env` файла (`VK_CONFIRMATION_CODE`)
6. Сохраните изменения

## 📦 Структура установки

После установки проект будет расположен по пути `/opt/anton-maker` со следующей структурой:
```
/opt/anton-maker/
├── venv/                   # Виртуальное окружение Python
├── manage.py               # Django-менеджер
├── config/                 # Настройки Django
├── crm/                    # Приложение CRM
├── templates/              # Шаблоны
├── deploy/                 # Скрипты развёртывания
├── data/                   # Постоянные данные
│   ├── db.sqlite3          # База данных
│   ├── static/             # Статические файлы
│   └── media/              # Загруженные файлы
└── gunicorn.sock           # Unix socket Gunicorn
```

## 🔧 Управление сервисом

### Статус сервиса
```bash
systemctl status anton-maker
```

### Логи приложения
```bash
journalctl -u anton-maker -f
```

### Перезапуск сервиса
```bash
systemctl restart anton-maker
```

### Остановка/запуск сервиса
```bash
systemctl stop anton-maker
systemctl start anton-maker
```

## 🧪 Проверка установки

После завершения установки проверьте работу сервиса:

1. **Проверка HTTP-ответа**:
```bash
curl -I http://anton-maker.ru
curl -I https://anton-maker.ru
```

2. **Проверка админки**:
   - Откройте `https://anton-maker.ru/admin/`
   - Используйте учётные данные из команды создания суперпользователя

3. **Проверка калькулятора**:
   - Откройте `https://anton-maker.ru/calculator/`

4. **Проверка вебхука ВК**:
```bash
curl -X POST https://anton-maker.ru/webhook/ \
  -H "Content-Type: application/json" \
  -d '{"type":"confirmation"}'
```
Должно вернуться значение из `VK_CONFIRMATION_CODE`.

## 🔄 Обновление проекта

Для обновления проекта до последней версии выполните:
```bash
cd /opt/anton-maker
git pull origin main
source venv/bin/activate
pip install -r requirements.txt
python manage.py migrate
python manage.py collectstatic --noinput
systemctl restart anton-maker
```

## 🐛 Устранение неполадок

### Приложение не запускается
- Проверьте логи: `journalctl -u anton-maker -f`
- Убедитесь, что все зависимости установлены: `source venv/bin/activate && pip list`
- Проверьте права доступа к директориям в `/opt/anton-maker/data/`

### SSL не работает
- Проверьте, что домен правильно направлен на IP-адрес сервера
- Убедитесь, что порты 80/443 открыты
- Проверьте конфигурацию Nginx: `nginx -t`

### Вебхук ВК не отвечает
- Убедитесь, что URL в настройках сообщества соответствует `https://anton-maker.ru/webhook/`
- Проверьте, что `VK_CONFIRMATION_CODE` указан верно
- Убедитесь, что Nginx проксирует запросы на Gunicorn

### Ошибка "Database is locked"
- Убедитесь, что WAL-режим включён: откройте SQLite и выполните `PRAGMA journal_mode;` (должно вернуть `wal`)
- Проверьте, что нет других процессов, блокирующих БД
- При необходимости увеличьте timeout в настройках БД

## 📊 Мониторинг и обслуживание

### CRON-задачи
Система включает автоматические задачи:
- Ежедневный отчёт в ВК (9:00)
- Еженедельный отчёт (понедельник 10:00)
- Проверка остатков материалов (каждый час)
- Резервное копирование (3:00)

Добавьте CRON-задачи из файла `deploy/cron.example`:
```bash
crontab -e
# Скопируйте содержимое из deploy/cron.example
```

### Резервное копирование
Скрипт `deploy/backup_db.sh` автоматически:
- Копирует базу данных с WAL-файлами
- Архивирует медиа-файлы
- Архивирует конфигурационные файлы
- Удаляет бэкапы старше 30 дней

### Логи
- Основное приложение: `journalctl -u anton-maker -f`
- Nginx: `/var/log/nginx/anton-maker-access.log`, `/var/log/nginx/anton-maker-error.log`
- CRON-задачи: `/var/log/anton-maker/`

## 📞 Техническая поддержка

Для вопросов по установке и настройке обращайтесь:
- Email: support@anton-maker.ru
- ВКонтакте: https://vk.com/antonmaker

---
Документация по развёртыванию Anton Maker CRM. Версия 1.0
