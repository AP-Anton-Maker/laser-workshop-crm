# Laser CRM — Система управления лазерной мастерской

CRM-система и бот ВКонтакте для автоматизации заказов лазерной резки.  
Развернута на сервере **Beelink Mini S12 Pro** (Intel N100) под управлением **Proxmox** в Docker-контейнерах.

## 🚀 Особенности

- **Бот ВКонтакте**: Прием заказов 24/7 через Webhooks, загрузка макетов, уведомления.
- **Django Unfold**: Современная админ-панель с темной темой и кастомным калькулятором.
- **Оптимизация под NVMe**: SQLite в режиме WAL для высокой скорости записи.
- **Caddy Server**: Автоматический HTTPS, reverse proxy, раздача статики.
- **Печать**: Генерация маршрутных листов (А5) для производства.

## 📁 Структура проекта

```text
laser_project/
├── config/              # Настройки Django (settings, urls, wsgi)
├── crm/                 # Основное приложение
│   ├── models/          # БД: Клиенты, Заказы, Материалы
│   ├── admin/           # Интерфейс Unfold + Калькулятор
│   ├── bot_logic/       # Логика бота ВК (Webhooks, FSM)
│   └── management/      # Cron-задачи (ежедневный отчет)
├── templates/           # HTML шаблоны (калькулятор, печать)
├── data/                # Persistant storage (DB, Media, Static)
├── caddy/               # Конфиг Caddyfile
├── docker-compose.yml   # Оркестрация сервисов
└── .env                 # Секреты (токены, ключи)
```

## 🛠 Быстрый старт

1. **Клонирование и настройка**:
   ```bash
   cp .env.example .env
   # Отредактируйте .env, вставив VK_TOKEN и SECRET_KEY
   ```

2. **Запуск контейнеров**:
   ```bash
   docker compose up -d --build
   ```

3. **Создание суперпользователя**:
   ```bash
   docker compose exec web python manage.py createsuperuser
   ```

4. **Настройка вебхука ВК**:
   - Укажите в настройках группы ВК URL: `https://ваш-домен/bot/webhook/`
   - Вставьте `VK_CONFIRMATION_CODE` из `.env` в поле "Код подтверждения".

## 🔧 Технологии

- **Backend**: Python 3.10, Django 4.2+, Gunicorn
- **Frontend**: Django Unfold, Tailwind CSS (CDN)
- **Database**: SQLite3 (WAL mode)
- **Web Server**: Caddy (HTTPS), Docker Compose
- **API**: ВКонтакте API 5.131

## 📄 Документация

- [SERVER_SETUP.md](./SERVER_SETUP.md) — Инструкция по установке на Proxmox LXC.

## 📞 Контакты

Вопросы и предложения: администратор системы (через ВК или email).
