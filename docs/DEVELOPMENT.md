# Руководство разработчика PayGo

## Быстрый старт

### Подготовка окружения

1. **Клонирование репозитория:**
```bash
git clone <repository-url>
cd PayGo
```

2. **Установка Docker и Docker Compose:**
   - Следуйте инструкциям на официальном сайте Docker

### Запуск веб-сервиса

1. **Запуск всех сервисов:**
```bash
docker-compose up -d
```

2. **Доступ к сервисам:**
   - Frontend: http://localhost:3000
   - Backend API: http://localhost:8000
   - API Documentation: http://localhost:8000/docs
   - Database: localhost:5432

### Разработка терминала

1. **Установка зависимостей Python:**
```bash
cd terminal/
pip install -r requirements.txt
```

2. **Установка зависимостей C++:**
```bash
# Ubuntu/Debian
sudo apt-get install qtbase5-dev libopencv-dev cmake build-essential

# Arch Linux  
sudo pacman -S qt6-base opencv cmake

# macOS
brew install qt opencv cmake
```

3. **Сборка терминала:**
```bash
mkdir build && cd build
cmake ..
make
```

## Структура проекта

```
PayGo/
├── terminal/                 # Терминальное ПО
│   ├── src/                 # C++ исходники
│   ├── include/             # Заголовочные файлы
│   ├── gui/                 # Qt интерфейс
│   ├── biometry/            # Биометрические алгоритмы
│   ├── payments/            # Платежная логика
│   └── lib/                 # Библиотеки
├── web-service/             # Веб-сервис
│   ├── backend/             # FastAPI бэкенд
│   ├── frontend/            # React фронтенд
│   ├── api/                 # API документация
│   └── database/            # SQL схемы
├── config/                  # Конфигурация
├── docs/                    # Документация
└── tests/                   # Тесты
```

## Архитектура

### Терминал
- **Основа:** C++ + Qt для GUI
- **Биометрия:** Python + OpenCV + dlib
- **Коммуникация:** REST API + WebSocket
- **База данных:** SQLite (локальная)
- **Платформа:** Raspberry Pi 4 (ARM64 Linux)

### Веб-сервис
- **Backend:** Python FastAPI
- **Frontend:** React + TypeScript + Ant Design
- **База данных:** PostgreSQL + Redis
- **Аутентификация:** JWT + OAuth2
- **Развертывание:** Docker + Docker Compose

## API Спецификация

### Терминал → Сервер
```
POST /api/v1/transactions       # Создание транзакции
GET  /api/v1/terminal/config    # Получение конфигурации
POST /api/v1/terminal/heartbeat # Отправка статуса
```

### Клиент → Сервер
```
GET  /api/v1/user/profile       # Профиль пользователя
POST /api/v1/cards              # Добавление карты
GET  /api/v1/transactions       # История транзакций
```

## Безопасность

### Терминал
- Шифрование данных AES-256-GCM
- Подписывание транзакций
- Защищенное хранение ключей
- Liveness detection для биометрии

### Веб-сервис
- HTTPS только
- JWT токены с коротким временем жизни
- Rate limiting
- Input validation
- SQL injection protection

## Тестирование

### Юнит-тесты
```bash
# Python
pytest tests/

# C++ (будет настроено позже)
ctest
```

### Интеграционные тесты
```bash
docker-compose -f docker-compose.test.yml up --abort-on-container-exit
```

## Развертывание

### Development
```bash
docker-compose up -d
```

### Production
```bash
docker-compose -f docker-compose.prod.yml up -d
```

## Мониторинг

### Логи
- Терминал: `/var/log/paygo/terminal.log`
- Backend: Docker logs
- Frontend: Browser console

### Метрики
- Prometheus endpoint: `/metrics`
- Grafana dashboard: http://localhost:3001

## Интеграция с банками

### Тестовые среды
- **ВТБ:** https://sandbox.api.vtb.ru
- **Альфа-Банк:** https://test.payform.ru
- **Центр-Инвест:** https://test.centrinvest.ru

### Продакшн API
Конфигурация в `config/banks.json`

## Отладка

### Backend
```bash
docker-compose logs backend
```

### Frontend
```bash
docker-compose logs frontend
```

### Терминал
```bash
# Подключение к устройству
ssh pi@terminal-ip
tail -f /var/log/paygo/terminal.log
```

## Внесение изменений

1. Создайте feature branch
2. Внесите изменения
3. Добавьте тесты
4. Запустите полное тестирование
5. Создайте Pull Request

## Контакты

- Техническая поддержка: tech@paygo.ru
- Документация API: https://api.paygo.ru/docs
- Issue tracker: [GitHub Issues] 