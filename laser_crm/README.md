# 🚀 Laser CRM — Django + VK Bot + Docker

Профессиональная CRM-система для лазерной мастерской с интеграцией ВКонтакте, умным ботом-помощником и админ-панелью.

## ✨ Возможности

- **VK Бот**: Автоматический расчёт стоимости заказов (11 типов расчётов)
- **Админ-панель**: Управление клиентами, заказами, складом, промокодами
- **Чат с клиентом**: Прямая связь через VK из админки
- **Кэшбэк-система**: Автоматическое начисление бонусов
- **Docker**: Готовность к развёртыванию на Raspberry Pi или VPS
- **Cloudflare Tunnel**: Опциональная поддержка HTTPS и домена

## 📁 Структура проекта

```
laser_crm/
├── Dockerfile
├── docker-compose.yml
├── .env.example
├── requirements.txt
├── manage.py
├── laser_crm/          # Основной проект Django
├── bot/                # Приложение VK бота
├── templates/          # Шаблоны админки
└── static/             # Статические файлы
```

## 🚀 Быстрый старт

### 1. Клонирование и настройка

```bash
git clone https://github.com/yourusername/laser-crm.git
cd laser-crm
cp .env.example .env
```

### 2. Заполните `.env`

```env
VK_TOKEN=ваш_токен_сообщества
VK_GROUP_ID=123456789
SECRET_KEY=сгенерируйте_случайную_строку_40_символов
DEBUG=False
```

### 3. Запуск через Docker

```bash
docker compose up -d --build
docker compose exec web python manage.py migrate
docker compose exec web python manage.py createsuperuser
```

### 4. Доступ

- Админка: `http://localhost:8000/admin`
- Бот автоматически отвечает в вашем VK-сообществе

## 🛠 Технологии

- **Backend**: Django 4.2+
- **Bot**: vk-api, Long Polling
- **Database**: SQLite (для простоты), можно заменить на PostgreSQL
- **Deployment**: Docker, Docker Compose
- **Optional**: Cloudflare Tunnel для HTTPS

## 📝 Лицензия

MIT
