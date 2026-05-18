# Anton Maker CRM

CRM-система + VK Bot для лазерной мастерской.  
Стек: Django 4.2 + Gunicorn + Nginx + SQLite (WAL) + VK API.  
Без Docker. Прямой запуск на Debian 12 LXC.

## 🚀 Быстрый старт

### 1. Подготовка сервера (Debian 12 LXC)
```bash
apt update && apt install -y git curl nano
cd /opt
git clone <YOUR_REPO_URL> anton_maker
cd anton_maker
```

### 2. Настройка окружения
```bash
cp .env.example .env
nano .env
```

**Обязательные переменные:**
- `SECRET_KEY` — сгенерировать: `python3 -c "import secrets; print(secrets.token_urlsafe(50))"`
- `DEBUG=False`
- `ALLOWED_HOSTS` — ваш домен и IP
- `VK_TOKEN` — токен сообщества VK
- `VK_CONFIRMATION_CODE` — код подтверждения из настроек VK
- `VK_SECRET_KEY` — любой сложный секрет для вебхука
- `VK_ADMIN_ID` — ваш VK ID для уведомлений
- `SITE_URL` — https://вашдомен.ru

### 3. Установка
```bash
bash deploy/install.sh
python3 manage.py createsuperuser
```

### 4. SSL сертификат
```bash
apt install -y certbot python3-certbot-nginx
certbot --nginx -d вашдомен.ru
systemctl reload nginx
```

### 5. Настройка VK Webhook
1. Управление сообществом → Работа с API → Webhook
2. Адрес: `https://вашдомен.ru/bot/webhook/`
3. Секретный ключ: значение `VK_SECRET_KEY` из `.env`
4. Включить события: `message_new`
5. Сохранить

### 6. Запуск
```bash
systemctl restart anton-maker
systemctl status anton-maker
```

## 📁 Структура проекта

```
anton_maker/
├── config/              # Настройки Django
├── crm/                 # Основное приложение
│   ├── admin/           # Админка (Unfold)
│   ├── bot_logic/       # Логика VK бота
│   ├── models/          # Модели данных
│   ├── utils/           # Утилиты
│   └── management/      # Cron-команды
├── deploy/              # Скрипты деплоя
├── templates/           # HTML шаблоны
├── data/                # БД, медиа, статика
└── manage.py
```

## 🔧 Управление

### Админка
Доступна по: `https://вашдомен.ru/secret-admin/`

### Бэкапы
```bash
chmod +x deploy/backup.sh
crontab -e
# Добавить: 0 3 * * * /opt/anton_maker/deploy/backup.sh
```

### Обновление
```bash
cd /opt/anton_maker
git pull
source venv/bin/activate
python manage.py migrate && python manage.py collectstatic --noinput
systemctl restart anton-maker
```

### Логи
```bash
journalctl -u anton-maker -f
tail -f /var/log/nginx/error.log
```

## 🛠️ Команды управления

```bash
# Ежедневная сводка
python manage.py daily_briefing

# Проверка остатков
python manage.py check_stock
```

## 📄 Лицензия

Проприетарное ПО. Все права защищены.
