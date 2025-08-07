# PayGo API Documentation

## Обзор

PayGo API предоставляет полный набор эндпоинтов для управления системой платежных терминалов, включая аутентификацию пользователей, управление картами, обработку транзакций и администрирование.

## Базовый URL

```
Production: https://api.paygo.ru/api/v1
Development: http://localhost:8000/api/v1
```

## Аутентификация

API использует JWT токены для аутентификации. Токен должен быть включен в заголовок `Authorization`:

```
Authorization: Bearer <your-jwt-token>
```

## Эндпоинты

### Аутентификация

#### POST /auth/login
Вход в систему

**Запрос:**
```json
{
  "email": "user@example.com",
  "password": "password123",
  "remember_me": false
}
```

**Ответ:**
```json
{
  "access_token": "eyJ0eXAiOiJKV1QiLCJhbGciOiJIUzI1NiJ9...",
  "refresh_token": "eyJ0eXAiOiJKV1QiLCJhbGciOiJIUzI1NiJ9...",
  "token_type": "bearer",
  "expires_in": 1800,
  "user": {
    "id": "user123",
    "email": "user@example.com",
    "full_name": "Иван Иванов",
    "role": "user"
  }
}
```

#### POST /auth/logout
Выход из системы

#### POST /auth/refresh
Обновление токена доступа

#### POST /auth/biometric
Биометрическая аутентификация

**Запрос:**
```json
{
  "user_id": "user123",
  "biometric_type": "fingerprint",
  "template_data": "encrypted_biometric_data"
}
```

### Пользователи

#### GET /users/profile
Получение профиля текущего пользователя

#### PUT /users/profile
Обновление профиля пользователя

#### POST /users/change-password
Изменение пароля

#### GET /users/notification-settings
Получение настроек уведомлений

#### PUT /users/notification-settings
Обновление настроек уведомлений

### Карты

#### GET /cards
Получение списка карт пользователя

**Ответ:**
```json
{
  "cards": [
    {
      "id": "card123",
      "masked_number": "**** **** **** 1234",
      "bank_name": "Сбербанк",
      "card_type": "debit",
      "is_primary": true,
      "expires_at": "2025-12-31",
      "created_at": "2023-01-01T00:00:00Z"
    }
  ]
}
```

#### POST /cards
Добавление новой карты

**Запрос:**
```json
{
  "card_number": "1234567890123456",
  "expiry_month": 12,
  "expiry_year": 2025,
  "cvv": "123",
  "cardholder_name": "IVAN IVANOV"
}
```

#### DELETE /cards/{card_id}
Удаление карты

#### PUT /cards/{card_id}/set-primary
Установка карты как основной

### Транзакции

#### GET /transactions
Получение истории транзакций

**Параметры запроса:**
- `page` (int): Номер страницы
- `limit` (int): Количество записей на странице
- `start_date` (date): Начальная дата
- `end_date` (date): Конечная дата
- `status` (string): Статус транзакции

**Ответ:**
```json
{
  "transactions": [
    {
      "id": "txn123",
      "amount": 1500.00,
      "currency": "RUB",
      "status": "completed",
      "terminal_id": "terminal456",
      "card_id": "card123",
      "created_at": "2023-08-15T14:30:00Z",
      "description": "Покупка в магазине"
    }
  ],
  "pagination": {
    "page": 1,
    "limit": 20,
    "total": 150,
    "pages": 8
  }
}
```

#### POST /transactions
Создание новой транзакции

#### GET /transactions/{transaction_id}
Получение деталей транзакции

#### POST /transactions/{transaction_id}/refund
Возврат транзакции

### Терминалы

#### GET /terminals
Получение списка терминалов

**Ответ:**
```json
{
  "terminals": [
    {
      "id": "terminal123",
      "name": "Терминал №1",
      "location": "Торговый центр 'Горизонт'",
      "address": "ул. Пушкинская, 10",
      "status": "online",
      "supported_payment_methods": ["nfc", "qr_code", "biometric"],
      "last_ping": "2023-08-15T14:30:00Z"
    }
  ]
}
```

#### GET /terminals/{terminal_id}
Получение информации о терминале

#### GET /terminals/{terminal_id}/stats
Получение статистики терминала

#### POST /terminals/{terminal_id}/commands
Отправка команды терминалу

### Администрирование

#### GET /admin/dashboard
Получение данных для панели администратора

#### GET /admin/users
Управление пользователями (только для администраторов)

#### GET /admin/terminals
Управление терминалами

#### GET /admin/system-health
Проверка состояния системы

## Коды ошибок

| Код | Описание |
|-----|----------|
| 400 | Неверный запрос |
| 401 | Не авторизован |
| 403 | Доступ запрещен |
| 404 | Ресурс не найден |
| 422 | Ошибка валидации |
| 500 | Внутренняя ошибка сервера |

## Примеры ошибок

```json
{
  "detail": "Недостаточно прав доступа",
  "error_code": "INSUFFICIENT_PERMISSIONS",
  "timestamp": "2023-08-15T14:30:00Z"
}
```

## WebSocket соединения

### /ws/terminals/{terminal_id}
Реальное время для мониторинга терминала

### /ws/notifications
Уведомления пользователя в реальном времени

## SDK и библиотеки

- **Python**: `pip install paygo-python-sdk`
- **JavaScript**: `npm install paygo-js-sdk`
- **C++**: Для интеграции с терминалами

## Поддержка

- Email: support@paygo.ru
- Документация: https://docs.paygo.ru
- GitHub: https://github.com/paygo/api 