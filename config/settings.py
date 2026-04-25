import os
from pathlib import Path
from dotenv import load_dotenv

# Загружаем секретные данные из .env
load_dotenv()

# Базовая директория (корневая папка laser_project)
BASE_DIR = Path(__file__).resolve().parent.parent

# Секретные ключи из .env
SECRET_KEY = os.getenv('SECRET_KEY', 'default-unsafe-key')
DEBUG = os.getenv('DEBUG', 'True') == 'True'

ALLOWED_HOSTS = ['*'] # Позже тут укажем IP Малинки

# ПРИЛОЖЕНИЯ
INSTALLED_APPS = [
    "unfold",  # Красивая тема (обязательно ПЕРЕД стандартной админкой)
    "django.contrib.admin",
    "django.contrib.auth",
    "django.contrib.contenttypes",
    "django.contrib.sessions",
    "django.contrib.messages",
    "django.contrib.staticfiles",
    
    "crm",  # Наш главный модуль бизнес-логики (создадим в Шаге 3)
]

MIDDLEWARE = [
    "django.middleware.security.SecurityMiddleware",
    "django.contrib.sessions.middleware.SessionMiddleware",
    "django.middleware.common.CommonMiddleware",
    "django.middleware.csrf.CsrfViewMiddleware",
    "django.contrib.auth.middleware.AuthenticationMiddleware",
    "django.contrib.messages.middleware.MessageMiddleware",
    "django.middleware.clickjacking.XFrameOptionsMiddleware",
]

ROOT_URLCONF = "config.urls"
WSGI_APPLICATION = "config.wsgi.application"

TEMPLATES = [
    {
        "BACKEND": "django.template.backends.django.DjangoTemplates",
        "DIRS": [BASE_DIR / "templates"], # Папка для кастомных шаблонов (ТЗ, калькулятор)
        "APP_DIRS": True,
        "OPTIONS": {
            "context_processors": [
                "django.template.context_processors.debug",
                "django.template.context_processors.request",
                "django.contrib.auth.context_processors.auth",
                "django.contrib.messages.context_processors.messages",
            ],
        },
    },
]

# БАЗА ДАННЫХ (SQLite идеален для соло-проекта и Raspberry)
# Сохраняем строго в папку data/, чтобы не потерять при перезапуске!
# Оптимизация для NVMe SSD: WAL режим + нормальная синхронизация
DATABASES = {
    "default": {
        "ENGINE": "django.db.backends.sqlite3",
        "NAME": BASE_DIR / "data" / "db.sqlite3",
        "OPTIONS": {
            "init_command": (
                "PRAGMA journal_mode=WAL; "
                "PRAGMA synchronous=NORMAL; "
                "PRAGMA cache_size=10000; "
                "PRAGMA temp_store=MEMORY;"
            )
        }
    }
}

# ЯЗЫК И ВРЕМЯ (Ставим русский язык и Московское время)
LANGUAGE_CODE = "ru-ru"
TIME_ZONE = "Europe/Moscow"
USE_I18N = True
USE_TZ = True

# СТАТИКА И МЕДИА (Стили админки и файлы клиентов)
# Тоже храним в data/, чтобы при обновлении системы файлы не удалились
STATIC_URL = "static/"
STATIC_ROOT = BASE_DIR / "data" / "static"

MEDIA_URL = "media/"
MEDIA_ROOT = BASE_DIR / "data" / "media"

DEFAULT_AUTO_FIELD = "django.db.models.BigAutoField"

# НАСТРОЙКИ НАШЕГО БОТА ВК
VK_TOKEN = os.getenv('VK_TOKEN')
VK_GROUP_ID = os.getenv('VK_GROUP_ID')
VK_ADMIN_ID = os.getenv('VK_ADMIN_ID')
VK_CONFIRMATION_CODE = os.getenv('VK_CONFIRMATION_CODE', '')

# НАСТРОЙКА КРАСИВОЙ АДМИНКИ UNFOLD
UNFOLD = {
    "SITE_TITLE": "Лазерная Мастерская",
    "SITE_HEADER": "Управление мастерской",
    "COLORS": {
        "primary": {
            "50": "250 245 255",
            "100": "243 232 255",
            "500": "168 85 247", # Приятный фиолетовый акцент
            "600": "147 51 234",
            "700": "126 34 206",
            "900": "88 28 135",
        },
    },
}
