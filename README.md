# Laser CRM — CRM и бот ВКонтакте для лазерной мастерской

[![License: MIT](https://img.shields.io/badge/License-MIT-yellow.svg)](https://opensource.org/licenses/MIT)
[![Django](https://img.shields.io/badge/Django-4.2-green.svg)](https://www.djangoproject.com/)
[![Docker](https://img.shields.io/badge/Docker-Ready-blue.svg)](https://www.docker.com/)

**Laser CRM** — это система для автоматизации лазерной мастерской (резка, гравировка, маркировка). Проект объединяет:

- 🤖 **VK-бота** с калькулятором стоимости, FSM-диалогами и кэшбэком
- 🖥️ **Админку Django** с управлением заказами, клиентами и складом
- 🐳 **Docker** для простого развёртывания на сервере Beelink S12 Pro (Proxmox LXC)

---

## ✨ Возможности

### Для клиента (в VK)
- **Рассчёт стоимости** — 11 типов калькулятора (площадь, длина реза, глубина гравировки и др.)
- **Баланс кэшбэка** — начисление 5% за каждый заказ
- **Связаться с мастером** — отправка вопросов и макетов

### Для мастера (админка Django)
- **Управление заказами** — статусы (новый, в работе, готов, выдан)
- **Клиенты** — авто-создание из VK, история заказов
- **Склад материалов** — учёт остатков
- **Чат с клиентом** — встроенный мессенджер

---

## 🛠️ Технологии

- Python 3.10
- Django 4.2 + django-unfold
- VK API (vk-api)
- SQLite (WAL режим для NVMe SSD)
- Docker + Docker Compose
- Gunicorn (2 workers, 4 threads)
- Caddy (reverse proxy + HTTPS)

---

## 📦 Требования

- Сервер Beelink S12 Pro (Intel N100) с Proxmox VE
- Docker и Docker Compose внутри LXC контейнера
- Группа ВКонтакте с токеном доступа
- Домен для HTTPS (опционально)

---

## 🚀 Быстрый старт

```bash
# Клонируйте репозиторий
git clone <repository_url>
cd laser_project

# Создайте .env файл
cp .env.example .env
nano .env  # Заполните токены и настройки

# Запустите контейнеры
docker compose up -d --build

# Примените миграции
docker compose exec web python manage.py migrate

# Создайте суперпользователя
docker compose exec web python manage.py createsuperuser
```

Админка: `https://ваш-домен/admin`

---

## 📁 Структура проекта

```
laser_project/
├── .env                      # Секретные ключи
├── docker-compose.yml        # Сервисы web и caddy
├── Dockerfile                # Образ Python 3.10
├── entrypoint.sh             # Скрипт запуска
├── requirements.txt          # Зависимости Python
├── caddy/
│   └── Caddyfile            # Reverse proxy + статика
├── data/                     # Персистентные данные (БД, media, static)
├── config/                   # Настройки Django
└── crm/                      # Основное приложение
    ├── models/               # Клиенты, Заказы, Склад
    ├── admin/                # Интерфейс Unfold
    └── bot_logic/            # Логика VK бота (Webhooks)
```

---

## 🔧 Обновление

```bash
git pull
docker compose down
docker compose up -d --build
docker compose exec web python manage.py migrate
```

---

## 📄 Лицензия

MIT

---

**Laser CRM** — автоматизация для лазерных мастерских 🚀
