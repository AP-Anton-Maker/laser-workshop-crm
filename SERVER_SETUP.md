# Настройка сервера Beelink S12 Pro (Intel N100) на Proxmox VE

## Оборудование

- **Сервер**: Beelink Mini S12 Pro
- **Процессор**: Intel N100 (x86_64, 4 ядра, 6 потоков)
- **ОЗУ**: 16 ГБ DDR5 (рекомендуется)
- **Накопитель**: NVMe SSD 500 ГБ+ (для БД и файлов)
- **Гипервизор**: Proxmox VE 8.x

---

## 1. Установка Proxmox VE

1. Скачайте ISO образ с [официального сайта](https://www.proxmox.com/en/downloads)
2. Запишите на флешку (Rufus / balenaEtcher)
3. Установите на NVMe SSD Beelink
4. После установки откройте веб-интерфейс: `https://IP-адрес:8006`

---

## 2. Создание LXC контейнера для Docker

### Шаг 2.1: Подготовка шаблона

```bash
# В shell хоста Proxmox скачайте шаблон Ubuntu
pveam download local ubuntu-22.04-standard_22.04-1_amd64.tar.gz
```

### Шаг 2.2: Создание контейнера

1. В веб-интерфейсе Proxmox нажмите **Create CT**
2. **General**:
   - Hostname: `laser-crm`
   - Password: `<ваш_пароль>`
3. **Template**: Выберите `ubuntu-22.04-standard`
4. **Disk**: 
   - Size: `32 GB` (минимум)
   - Storage: `local-lvm` или NVMe
5. **CPU**: 
   - Cores: `2`
   - Type: `host` (для лучшей производительности)
6. **Memory**: 
   - Memory: `4096 MB`
   - Swap: `512 MB`
7. **Network**: 
   - IPv4: DHCP или статический IP
   - Bridge: `vmbr0`
8. **Confirm**: Готово

### Шаг 2.3: Настройка привилегий для Docker

В shell хоста Proxmox выполните:

```bash
# Редактируем конфиг контейнера (CTID замените на ваш, например 100)
nano /etc/pve/lxc/100.conf
```

Добавьте строки для поддержки Docker внутри LXC:

```conf
lxc.apparmor.profile: unconfined
lxc.cap.drop:
lxc.cgroup.devices.allow: a
lxc.mount.auto: cgroup:rw
```

Перезапустите контейнер:

```bash
pct restart 100
```

---

## 3. Установка Docker внутри LXC

Подключитесь к контейтеру через консоль Proxmox или SSH:

```bash
# Обновите пакеты
apt update && apt upgrade -y

# Установите Docker
curl -fsSL https://get.docker.com | sh

# Добавьте пользователя в группу docker
usermod -aG docker $USER

# Установите Docker Compose
apt install docker-compose-plugin -y

# Проверка
docker --version
docker compose version
```

---

## 4. Развёртывание проекта Laser CRM

### Шаг 4.1: Клонирование репозитория

```bash
cd /opt
git clone <repository_url> laser_project
cd laser_project
```

### Шаг 4.2: Настройка переменных окружения

```bash
cp .env.example .env
nano .env
```

Заполните:

```env
VK_TOKEN=<токен_сообщества_VK>
VK_GROUP_ID=<ID_группы>
VK_CONFIRMATION_CODE=<код_подтверждения>
SECRET_KEY=<сгенерируйте_командой>_python -c 'from django.core.management.utils import get_random_secret_key; print(get_random_secret_key())'
DOMAIN=ваш-домен.ru
```

### Шаг 4.3: Создание папки data

```bash
mkdir -p data/db data/static data/media
chmod -R 755 data
```

### Шаг 4.4: Запуск контейнеров

```bash
docker compose up -d --build
```

### Шаг 4.5: Миграции и суперпользователь

```bash
docker compose exec web python manage.py migrate
docker compose exec web python manage.py createsuperuser
```

---

## 5. Настройка HTTPS (Caddy)

Caddy автоматически получает SSL-сертификаты Let's Encrypt.

### Вариант A: Публичный домен

Если у вас есть домен, направьте DNS A-запись на IP сервера:

```
A    @    <ваш_IP>
A    www  <ваш_IP>
```

Caddy сам получит сертификат при первом запуске.

### Вариант B: Локальная сеть (self-signed)

Caddy использует `tls internal` — сертификаты будут самоподписанными.  
Для доступа добавьте CA-сертификат в доверенные на клиентских устройствах.

---

## 6. Монтирование NVMe SSD (опционально)

Если хотите хранить данные на отдельном NVMe:

```bash
# На хосте Proxmox
lsblk  # Найдите NVMe диск (например, /dev/nvme0n1)

# Создайте файловую систему
mkfs.ext4 /dev/nvme0n1p1

# Смонтируйте
mkdir -p /mnt/nvme_data
mount /dev/nvme0n1p1 /mnt/nvme_data

# Пробросьте в LXC контейнер
# В веб-интерфейсе: CT > Resources > Mount Point > Add
# Path: /mnt/nvme_data
# Storage: local
```

В `docker-compose.yml` измените volume:

```yaml
volumes:
  - /mnt/nvme_data/laser_crm:/app/data
```

---

## 7. Автозапуск при старте сервера

В веб-интерфейсе Proxmox:

1. Выберите CT > **Options** > **Start at boot**: ✓ Enabled
2. **Startup Order**: установите приоритет (например, 2)

---

## 8. Мониторинг и логи

```bash
# Просмотр логов контейнеров
docker compose logs -f web
docker compose logs -f caddy

# Статус сервисов
docker compose ps

# Использование ресурсов
docker stats
```

---

## 9. Резервное копирование

### Бэкап базы данных

```bash
# Внутри контейнера
docker compose exec web cp /app/data/db.sqlite3 /tmp/db_backup_$(date +%F).sqlite3

# Скопируйте на хост
docker compose exec web cat /app/data/db.sqlite3 > backup_$(date +%F).sqlite3
```

### Бэкап через Proxmox

Веб-интерфейс Proxmox > CT > **Backup** > **Backup now**  
Расписание: ежедневно в 02:00

---

## 10. Обновление проекта

```bash
cd /opt/laser_project
git pull
docker compose down
docker compose up -d --build
docker compose exec web python manage.py migrate
```

---

## 🔧 Полезные команды Proxmox

```bash
# Перезапуск контейнера
pct restart 100

# Консоль контейнера
pct enter 100

# Статус
pct status 100

# Бэкап
pct backup 100
```

---

## 📊 Рекомендуемые ресурсы для LXC

| Ресурс | Значение |
|--------|----------|
| CPU Cores | 2 |
| RAM | 4 ГБ |
| Disk | 32 ГБ+ |
| Network | vmbr0 (bridge) |

---

## ⚠️ Возможные проблемы

### Ошибка "permission denied" при монтировании volumes

Решение: Добавьте в `/etc/pve/lxc/CTID.conf`:

```conf
lxc.apparmor.profile: unconfined
```

### Docker не запускается внутри LXC

Проверьте, что включена поддержка nested virtualization:

```bash
# На хосте Proxmox
echo "options kvm_intel nested=1" >> /etc/modprobe.d/kvm.conf
```

### Caddy не получает SSL-сертификат

Проверьте, что порты 80 и 443 открыты и доступны из интернета:

```bash
iptables -L -n | grep -E '80|443'
```

---

**Готово!** Ваша CRM работает на Beelink S12 Pro с Proxmox 🚀
