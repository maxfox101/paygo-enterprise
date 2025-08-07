-- PayGo Database Initialization Script
-- Создание базы данных и пользователя для системы PayGo

-- Создание базы данных (если не существует)
CREATE DATABASE paygo_db WITH 
    ENCODING 'UTF8'
    LC_COLLATE = 'ru_RU.UTF-8'
    LC_CTYPE = 'ru_RU.UTF-8'
    TEMPLATE template0;

-- Создание пользователя для приложения
CREATE USER paygo_user WITH PASSWORD 'paygo_password';

-- Предоставление прав пользователю
GRANT ALL PRIVILEGES ON DATABASE paygo_db TO paygo_user;

-- Подключение к созданной базе данных
\c paygo_db;

-- Создание расширений
CREATE EXTENSION IF NOT EXISTS "uuid-ossp";
CREATE EXTENSION IF NOT EXISTS "pgcrypto";

-- Создание схемы для приложения
CREATE SCHEMA IF NOT EXISTS paygo;

-- Предоставление прав на схему
GRANT ALL ON SCHEMA paygo TO paygo_user;
GRANT ALL ON SCHEMA public TO paygo_user;

-- Таблица пользователей
CREATE TABLE IF NOT EXISTS users (
    id SERIAL PRIMARY KEY,
    email VARCHAR(255) UNIQUE NOT NULL,
    phone VARCHAR(20) UNIQUE NOT NULL,
    full_name VARCHAR(255) NOT NULL,
    hashed_password VARCHAR(255) NOT NULL,
    role VARCHAR(50) DEFAULT 'user' NOT NULL,
    is_active BOOLEAN DEFAULT TRUE,
    is_verified BOOLEAN DEFAULT FALSE,
    two_factor_enabled BOOLEAN DEFAULT FALSE,
    failed_login_attempts INTEGER DEFAULT 0,
    is_locked BOOLEAN DEFAULT FALSE,
    date_of_birth TIMESTAMP NULL,
    avatar_url VARCHAR(500) NULL,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    last_login TIMESTAMP NULL
);

-- Таблица банковских карт
CREATE TABLE IF NOT EXISTS cards (
    id SERIAL PRIMARY KEY,
    user_id INTEGER REFERENCES users(id) ON DELETE CASCADE,
    masked_number VARCHAR(19) NOT NULL,
    bank_name VARCHAR(100) NOT NULL,
    card_type VARCHAR(20) NOT NULL CHECK (card_type IN ('debit', 'credit')),
    is_primary BOOLEAN DEFAULT FALSE,
    expires_at TIMESTAMP NOT NULL,
    token VARCHAR(255) NOT NULL,
    is_active BOOLEAN DEFAULT TRUE,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

-- Таблица терминалов
CREATE TABLE IF NOT EXISTS terminals (
    id SERIAL PRIMARY KEY,
    serial_number VARCHAR(50) UNIQUE NOT NULL,
    name VARCHAR(255) NOT NULL,
    location VARCHAR(255) NOT NULL,
    address TEXT NOT NULL,
    latitude DECIMAL(10, 8) NULL,
    longitude DECIMAL(11, 8) NULL,
    terminal_type VARCHAR(50) NOT NULL CHECK (terminal_type IN ('standalone', 'integrated', 'mobile')),
    status VARCHAR(20) DEFAULT 'offline' CHECK (status IN ('online', 'offline', 'maintenance', 'error')),
    model VARCHAR(100) NOT NULL,
    manufacturer VARCHAR(100) NOT NULL,
    software_version VARCHAR(50) NULL,
    supported_payment_methods JSONB NULL,
    hardware_info JSONB NULL,
    configuration JSONB NULL,
    is_active BOOLEAN DEFAULT TRUE,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    last_ping TIMESTAMP NULL
);

-- Таблица транзакций
CREATE TABLE IF NOT EXISTS transactions (
    id SERIAL PRIMARY KEY,
    user_id INTEGER REFERENCES users(id) ON DELETE CASCADE,
    card_id INTEGER REFERENCES cards(id) ON DELETE SET NULL,
    terminal_id INTEGER REFERENCES terminals(id) ON DELETE SET NULL,
    amount DECIMAL(10, 2) NOT NULL CHECK (amount > 0),
    currency VARCHAR(3) DEFAULT 'RUB',
    status VARCHAR(20) NOT NULL CHECK (status IN ('pending', 'completed', 'failed', 'cancelled', 'refunded')),
    payment_method VARCHAR(20) NOT NULL CHECK (payment_method IN ('nfc', 'qr_code', 'biometric', 'card_insert')),
    description TEXT NULL,
    receipt_url VARCHAR(500) NULL,
    external_transaction_id VARCHAR(255) NULL,
    bank_response JSONB NULL,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    completed_at TIMESTAMP NULL
);

-- Таблица биометрических шаблонов
CREATE TABLE IF NOT EXISTS biometric_templates (
    id SERIAL PRIMARY KEY,
    user_id INTEGER REFERENCES users(id) ON DELETE CASCADE,
    template_type VARCHAR(20) NOT NULL CHECK (template_type IN ('fingerprint', 'face', 'voice')),
    template_data TEXT NOT NULL, -- Зашифрованные биометрические данные
    is_active BOOLEAN DEFAULT TRUE,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

-- Таблица настроек уведомлений
CREATE TABLE IF NOT EXISTS notification_settings (
    id SERIAL PRIMARY KEY,
    user_id INTEGER REFERENCES users(id) ON DELETE CASCADE UNIQUE,
    push_notifications BOOLEAN DEFAULT TRUE,
    sms_notifications BOOLEAN DEFAULT TRUE,
    email_notifications BOOLEAN DEFAULT FALSE,
    transaction_alerts BOOLEAN DEFAULT TRUE,
    security_alerts BOOLEAN DEFAULT TRUE,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

-- Таблица логов терминалов
CREATE TABLE IF NOT EXISTS terminal_logs (
    id SERIAL PRIMARY KEY,
    terminal_id INTEGER REFERENCES terminals(id) ON DELETE CASCADE,
    level VARCHAR(10) NOT NULL CHECK (level IN ('DEBUG', 'INFO', 'WARNING', 'ERROR')),
    message TEXT NOT NULL,
    component VARCHAR(50) NULL,
    additional_data JSONB NULL,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

-- Таблица сессий пользователей
CREATE TABLE IF NOT EXISTS user_sessions (
    id SERIAL PRIMARY KEY,
    user_id INTEGER REFERENCES users(id) ON DELETE CASCADE,
    token_hash VARCHAR(255) NOT NULL,
    expires_at TIMESTAMP NOT NULL,
    is_active BOOLEAN DEFAULT TRUE,
    ip_address INET NULL,
    user_agent TEXT NULL,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

-- Таблица команд для терминалов
CREATE TABLE IF NOT EXISTS terminal_commands (
    id SERIAL PRIMARY KEY,
    terminal_id INTEGER REFERENCES terminals(id) ON DELETE CASCADE,
    command_type VARCHAR(50) NOT NULL,
    command_data JSONB NOT NULL,
    status VARCHAR(20) DEFAULT 'pending' CHECK (status IN ('pending', 'executing', 'completed', 'failed')),
    result TEXT NULL,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    executed_at TIMESTAMP NULL
);

-- Создание индексов для оптимизации
CREATE INDEX IF NOT EXISTS idx_users_email ON users(email);
CREATE INDEX IF NOT EXISTS idx_users_phone ON users(phone);
CREATE INDEX IF NOT EXISTS idx_cards_user_id ON cards(user_id);
CREATE INDEX IF NOT EXISTS idx_cards_is_primary ON cards(is_primary) WHERE is_primary = TRUE;
CREATE INDEX IF NOT EXISTS idx_terminals_status ON terminals(status);
CREATE INDEX IF NOT EXISTS idx_terminals_serial_number ON terminals(serial_number);
CREATE INDEX IF NOT EXISTS idx_transactions_user_id ON transactions(user_id);
CREATE INDEX IF NOT EXISTS idx_transactions_terminal_id ON transactions(terminal_id);
CREATE INDEX IF NOT EXISTS idx_transactions_status ON transactions(status);
CREATE INDEX IF NOT EXISTS idx_transactions_created_at ON transactions(created_at);
CREATE INDEX IF NOT EXISTS idx_biometric_templates_user_id ON biometric_templates(user_id);
CREATE INDEX IF NOT EXISTS idx_terminal_logs_terminal_id ON terminal_logs(terminal_id);
CREATE INDEX IF NOT EXISTS idx_terminal_logs_created_at ON terminal_logs(created_at);
CREATE INDEX IF NOT EXISTS idx_user_sessions_user_id ON user_sessions(user_id);
CREATE INDEX IF NOT EXISTS idx_user_sessions_token_hash ON user_sessions(token_hash);

-- Создание триггеров для автоматического обновления updated_at
CREATE OR REPLACE FUNCTION update_updated_at_column()
RETURNS TRIGGER AS $$
BEGIN
    NEW.updated_at = CURRENT_TIMESTAMP;
    RETURN NEW;
END;
$$ language 'plpgsql';

CREATE TRIGGER update_users_updated_at BEFORE UPDATE ON users
    FOR EACH ROW EXECUTE FUNCTION update_updated_at_column();

CREATE TRIGGER update_cards_updated_at BEFORE UPDATE ON cards
    FOR EACH ROW EXECUTE FUNCTION update_updated_at_column();

CREATE TRIGGER update_terminals_updated_at BEFORE UPDATE ON terminals
    FOR EACH ROW EXECUTE FUNCTION update_updated_at_column();

CREATE TRIGGER update_biometric_templates_updated_at BEFORE UPDATE ON biometric_templates
    FOR EACH ROW EXECUTE FUNCTION update_updated_at_column();

CREATE TRIGGER update_notification_settings_updated_at BEFORE UPDATE ON notification_settings
    FOR EACH ROW EXECUTE FUNCTION update_updated_at_column();

-- Создание представлений для удобства
CREATE OR REPLACE VIEW user_cards_view AS
SELECT 
    u.id as user_id,
    u.full_name,
    u.email,
    c.id as card_id,
    c.masked_number,
    c.bank_name,
    c.card_type,
    c.is_primary,
    c.expires_at,
    c.is_active as card_active,
    c.created_at as card_created_at
FROM users u
LEFT JOIN cards c ON u.id = c.user_id
WHERE u.is_active = TRUE;

CREATE OR REPLACE VIEW terminal_stats_view AS
SELECT 
    t.id,
    t.name,
    t.location,
    t.status,
    COUNT(tr.id) as total_transactions,
    COALESCE(SUM(tr.amount), 0) as total_amount,
    COUNT(CASE WHEN tr.status = 'completed' THEN 1 END) as successful_transactions,
    COUNT(CASE WHEN tr.status = 'failed' THEN 1 END) as failed_transactions
FROM terminals t
LEFT JOIN transactions tr ON t.id = tr.terminal_id
GROUP BY t.id, t.name, t.location, t.status;

-- Предоставление прав на все таблицы пользователю приложения
GRANT ALL PRIVILEGES ON ALL TABLES IN SCHEMA public TO paygo_user;
GRANT ALL PRIVILEGES ON ALL SEQUENCES IN SCHEMA public TO paygo_user;
GRANT ALL PRIVILEGES ON ALL FUNCTIONS IN SCHEMA public TO paygo_user;

-- Вставка начальных данных
INSERT INTO users (email, phone, full_name, hashed_password, role, is_verified) VALUES
('nzosim@sfedu.ru', '+7 (928) 528-45-27', 'Никита Зосим Кириллович', '$2b$12$hashed_password_here', 'user', TRUE),
('admin@paygo.ru', '+7 (800) 555-01-01', 'Администратор PayGo', '$2b$12$admin_password_here', 'admin', TRUE)
ON CONFLICT (email) DO NOTHING;

-- Получение ID пользователя для связанных записей
DO $$
DECLARE
    user_id_var INTEGER;
BEGIN
    SELECT id INTO user_id_var FROM users WHERE email = 'nzosim@sfedu.ru';
    
    IF user_id_var IS NOT NULL THEN
        -- Вставка тестовых карт
        INSERT INTO cards (user_id, masked_number, bank_name, card_type, is_primary, expires_at, token) VALUES
        (user_id_var, '**** **** **** 5678', 'Т-банк', 'debit', TRUE, '2027-04-30', 'token_tbank_123'),
        (user_id_var, '**** **** **** 1234', 'ВТБ', 'debit', FALSE, '2026-08-31', 'token_vtb_456'),
        (user_id_var, '**** **** **** 9876', 'Альфа-банк', 'credit', FALSE, '2025-11-30', 'token_alfa_789')
        ON CONFLICT DO NOTHING;
        
        -- Вставка настроек уведомлений
        INSERT INTO notification_settings (user_id, push_notifications, sms_notifications, email_notifications) VALUES
        (user_id_var, TRUE, TRUE, FALSE)
        ON CONFLICT (user_id) DO NOTHING;
    END IF;
END $$;

-- Вставка тестовых терминалов
INSERT INTO terminals (serial_number, name, location, address, latitude, longitude, terminal_type, status, model, manufacturer, supported_payment_methods) VALUES
('PAYGO_001', 'Терминал №1', 'ТЦ Горизонт', 'ул. Пушкинская, 10, Ростов-на-Дону', 47.2357, 39.7015, 'standalone', 'online', 'PayGo-Pro-2025', 'PayGo Systems', '["nfc", "qr_code", "biometric"]'),
('PAYGO_002', 'Терминал №2', 'Супермаркет Магнит', 'пр. Ленина, 45, Ростов-на-Дону', 47.2280, 39.7100, 'integrated', 'online', 'PayGo-Lite-2025', 'PayGo Systems', '["nfc", "qr_code"]'),
('PAYGO_003', 'Терминал №3', 'Кафе Старбакс', 'ул. Большая Садовая, 123, Ростов-на-Дону', 47.2220, 39.7200, 'standalone', 'offline', 'PayGo-Pro-2025', 'PayGo Systems', '["nfc", "qr_code", "biometric"]'),
('PAYGO_004', 'Терминал №4', 'Аптека Ригла', 'ул. Социалистическая, 74, Ростов-на-Дону', 47.2150, 39.7050, 'integrated', 'maintenance', 'PayGo-Compact-2025', 'PayGo Systems', '["nfc"]'),
('PAYGO_005', 'Терминал №5', 'Автозаправка Лукойл', 'Московское шоссе, 15, Ростов-на-Дону', 47.2400, 39.6800, 'standalone', 'online', 'PayGo-Pro-2025', 'PayGo Systems', '["nfc", "qr_code", "biometric"]')
ON CONFLICT (serial_number) DO NOTHING;

COMMIT; 