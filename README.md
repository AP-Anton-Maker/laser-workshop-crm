# 🔬 Laser CRM: Enterprise-система для лазерной мастерской

[![Python](https://img.shields.io/badge/Python-3.9+-blue.svg)](https://www.python.org/)
[![FastAPI](https://img.shields.io/badge/FastAPI-0.109+-green.svg)](https://fastapi.tiangolo.com/)
[![SQLAlchemy](https://img.shields.io/badge/SQLAlchemy-2.0-red.svg)](https://www.sqlalchemy.org/)
[![AI](https://img.shields.io/badge/AI-Scikit--Learn-orange.svg)](https://scikit-learn.org/)
[![Platform](https://img.shields.io/badge/Platform-Raspberry%20Pi%203B%2B-green.svg)](https://www.raspberrypi.org/)

**Laser CRM** — это высокопроизводительная, асинхронная CRM-система уровня Enterprise, разработанная специально для автоматизации работы соло-предпринимателя в сфере лазерной резки и гравировки. 

Система объединяет полный цикл управления бизнесом: от точного расчета стоимости заказа (11 алгоритмов) и складского учета до интеграции с клиентами через ВКонтакте и прогнозирования выручки с помощью Искусственного Интеллекта. Проект оптимизирован для работы на компактном оборудовании (Raspberry Pi) без использования тяжелых контейнеров.

---

## ✨ Ключевые возможности

*   🧮 **Умный калькулятор:** Серверный расчет стоимости по 11 алгоритмам (площадь, периметр, время, 3D и др.) с защитой от подмены цены и автоматическими оптовыми скидками.
*   🤖 **VK-бот (VKBottle):** Полноценная интеграция с ВКонтакте. Бот сохраняет историю переписки в БД и позволяет менеджеру отвечать клиентам прямо из CRM.
*   🌴 **Режим "Отпуск":** Уникальная фича для соло-фаундеров. Включение тумблера в настройках заставляет бота автоматически отвечать клиентам кастомным сообщением о вашем отсутствии.
*   📈 **AI-прогноз выручки:** Модуль на базе `scikit-learn` (Linear Regression) анализирует тренды последних 30 дней и предсказывает доход на завтра.
*   💎 **Система лояльности:** Автоматическое начисление кэшбэка (5%) при завершении заказа и динамическая сегментация клиентов (New, Regular, VIP) на основе LTV.
*   🏭 **Складские алерты:** Контроль остатков материалов с подсветкой позиций, требующих срочной закупки (`low-stock`).
*   💾 **Бэкапы и Экспорт:** Мгновенное создание резервных копий SQLite базы данных и выгрузка отчетов (заказы, клиенты) в CSV формат.
*   🔒 **Безопасность:** JWT авторизация, хэширование паролей (bcrypt), строгая валидация данных через Pydantic.

---

## 🛠 Стек технологий

| Компонент | Технологии |
| :--- | :--- |
| **Backend** | Python 3.9+, FastAPI, SQLAlchemy 2.0 (Async), Pydantic v2, Uvicorn |
| **Database** | SQLite (aiosqlite) — легковесная, файловая БД |
| **AI & Math** | Scikit-learn, NumPy (для ML-прогнозов и расчетов) |
| **Integrations** | VKBottle (VKontakte API), PyJWT, Passlib (bcrypt) |
| **Frontend** | Vanilla JS (ES6 Modules), CSS3 (Variables, Grid/Flex), Chart.js |
| **DevOps** | Systemd, Nginx (Reverse Proxy + Static), UFW |

---

## 📂 Структура проекта

```text
laser_crm/
├── backend/
│   ├── api/                # Роутеры API (Auth, Orders, Clients, System...)
│   ├── core/               # Конфигурация и безопасность (JWT, Hashing)
│   ├── db/                 # Модели SQLAlchemy и сессии
│   ├── schemas/            # Pydantic схемы валидации
│   ├── services/           # Бизнес-логика (Calculator, AI, VK Bot, Backup)
│   ├── main.py             # Точка входа приложения
│   └── requirements.txt    # Зависимости Python
├── frontend/
│   ├── js/
│   │   ├── api/            # API клиенты (fetch wrappers с JWT)
│   │   ├── components/     # UI компоненты (Orders, Vacation settings)
│   │   ├── utils/          # Утилиты (Toasts)
│   │   ├── app.js          # Главная точка входа JS
│   │   └── router.js       # Навигация по вкладкам
│   ├── styles/             # Модульные CSS файлы
│   └── index.html          # Основной HTML шаблон
├── data/                   # Папка для БД и бэкапов (создается автоматически)
└── README.md
