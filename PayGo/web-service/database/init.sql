-- Инициализация базы данных PayGo
-- Создание расширений
CREATE EXTENSION IF NOT EXISTS "uuid-ossp";

-- Таблица пользователей
CREATE TABLE IF NOT EXISTS users (
    id SERIAL PRIMARY KEY,
    email VARCHAR(255) UNIQUE NOT NULL,
    phone VARCHAR(20) UNIQUE NOT NULL,
    full_name VARCHAR(255) NOT NULL,
    hashed_password VARCHAR(255) NOT NULL,
    role VARCHAR(20) DEFAULT 'user' NOT NULL,
    is_active BOOLEAN DEFAULT true,
    is_verified BOOLEAN DEFAULT false,
    avatar_url VARCHAR(500),
    created_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP,
    last_login TIMESTAMP WITH TIME ZONE
);

-- Таблица терминалов
CREATE TABLE IF NOT EXISTS terminals (
    id SERIAL PRIMARY KEY,
    terminal_id VARCHAR(50) UNIQUE NOT NULL,
    name VARCHAR(255) NOT NULL,
    location VARCHAR(255) NOT NULL,
    address TEXT,
    terminal_type VARCHAR(20) DEFAULT 'payment',
    status VARCHAR(20) DEFAULT 'offline',
    hardware_info JSONB,
    software_version VARCHAR(50),
    last_update TIMESTAMP WITH TIME ZONE,
    ip_address INET,
    mac_address VARCHAR(17),
    total_transactions INTEGER DEFAULT 0,
    total_amount NUMERIC(12,2) DEFAULT 0.0,
    config JSONB,
    created_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP,
    last_heartbeat TIMESTAMP WITH TIME ZONE
);

-- Таблица банковских карт
CREATE TABLE IF NOT EXISTS cards (
    id SERIAL PRIMARY KEY,
    user_id INTEGER REFERENCES users(id) ON DELETE CASCADE,
    card_token VARCHAR(255) UNIQUE NOT NULL,
    card_mask VARCHAR(50) NOT NULL,
    card_holder_name VARCHAR(100) NOT NULL,
    card_type VARCHAR(20) NOT NULL,
    payment_system VARCHAR(20) NOT NULL,
    bank_issuer VARCHAR(50) NOT NULL,
    is_active BOOLEAN DEFAULT true,
    is_primary BOOLEAN DEFAULT false,
    is_verified BOOLEAN DEFAULT false,
    expiry_month INTEGER,
    expiry_year INTEGER,
    created_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP,
    last_used TIMESTAMP WITH TIME ZONE
);

-- Таблица транзакций
CREATE TABLE IF NOT EXISTS transactions (
    id SERIAL PRIMARY KEY,
    transaction_id VARCHAR(100) UNIQUE NOT NULL,
    terminal_id INTEGER REFERENCES terminals(id) ON DELETE RESTRICT,
    user_id INTEGER REFERENCES users(id) ON DELETE SET NULL,
    amount NUMERIC(12,2) NOT NULL,
    currency VARCHAR(3) DEFAULT 'RUB',
    description TEXT,
    status VARCHAR(20) DEFAULT 'pending',
    payment_method VARCHAR(30) NOT NULL,
    bank_acquirer VARCHAR(50),
    bank_transaction_id VARCHAR(100),
    bank_response TEXT,
    card_mask VARCHAR(50),
    receipt_number VARCHAR(100),
    fiscal_data TEXT,
    created_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP,
    processed_at TIMESTAMP WITH TIME ZONE,
    completed_at TIMESTAMP WITH TIME ZONE
);

-- Индексы для производительности
CREATE INDEX IF NOT EXISTS idx_users_email ON users(email);
CREATE INDEX IF NOT EXISTS idx_users_phone ON users(phone);
CREATE INDEX IF NOT EXISTS idx_users_active ON users(is_active);

CREATE INDEX IF NOT EXISTS idx_terminals_terminal_id ON terminals(terminal_id);
CREATE INDEX IF NOT EXISTS idx_terminals_status ON terminals(status);
CREATE INDEX IF NOT EXISTS idx_terminals_location ON terminals(location);

CREATE INDEX IF NOT EXISTS idx_cards_user_id ON cards(user_id);
CREATE INDEX IF NOT EXISTS idx_cards_token ON cards(card_token);
CREATE INDEX IF NOT EXISTS idx_cards_primary ON cards(user_id, is_primary) WHERE is_primary = true;

CREATE INDEX IF NOT EXISTS idx_transactions_id ON transactions(transaction_id);
CREATE INDEX IF NOT EXISTS idx_transactions_terminal ON transactions(terminal_id);
CREATE INDEX IF NOT EXISTS idx_transactions_user ON transactions(user_id);
CREATE INDEX IF NOT EXISTS idx_transactions_status ON transactions(status);
CREATE INDEX IF NOT EXISTS idx_transactions_created ON transactions(created_at);
CREATE INDEX IF NOT EXISTS idx_transactions_amount ON transactions(amount);

-- Триггеры для автоматического обновления updated_at
CREATE OR REPLACE FUNCTION update_updated_at_column()
RETURNS TRIGGER AS $$
BEGIN
    NEW.updated_at = CURRENT_TIMESTAMP;
    RETURN NEW;
END;
$$ language 'plpgsql';

-- Применение триггеров
CREATE TRIGGER update_users_updated_at BEFORE UPDATE ON users 
    FOR EACH ROW EXECUTE FUNCTION update_updated_at_column();

CREATE TRIGGER update_terminals_updated_at BEFORE UPDATE ON terminals 
    FOR EACH ROW EXECUTE FUNCTION update_updated_at_column();

CREATE TRIGGER update_cards_updated_at BEFORE UPDATE ON cards 
    FOR EACH ROW EXECUTE FUNCTION update_updated_at_column();

-- Проверочные ограничения
ALTER TABLE users ADD CONSTRAINT check_role 
    CHECK (role IN ('user', 'admin', 'operator'));

ALTER TABLE terminals ADD CONSTRAINT check_terminal_type 
    CHECK (terminal_type IN ('payment', 'self_service', 'kiosk'));

ALTER TABLE terminals ADD CONSTRAINT check_status 
    CHECK (status IN ('online', 'offline', 'maintenance', 'error', 'blocked'));

ALTER TABLE cards ADD CONSTRAINT check_card_type 
    CHECK (card_type IN ('debit', 'credit', 'prepaid'));

ALTER TABLE cards ADD CONSTRAINT check_payment_system 
    CHECK (payment_system IN ('visa', 'mastercard', 'mir', 'unionpay'));

ALTER TABLE cards ADD CONSTRAINT check_expiry_month 
    CHECK (expiry_month >= 1 AND expiry_month <= 12);

ALTER TABLE transactions ADD CONSTRAINT check_amount 
    CHECK (amount > 0);

ALTER TABLE transactions ADD CONSTRAINT check_currency 
    CHECK (currency IN ('RUB', 'USD', 'EUR'));

ALTER TABLE transactions ADD CONSTRAINT check_status 
    CHECK (status IN ('pending', 'processing', 'completed', 'failed', 'cancelled', 'refunded'));

ALTER TABLE transactions ADD CONSTRAINT check_payment_method 
    CHECK (payment_method IN ('nfc_card', 'nfc_phone', 'qr_code', 'biometry_face', 'biometry_fingerprint'));

-- Создание начальных данных
INSERT INTO users (email, phone, full_name, hashed_password, role) VALUES 
('admin@paygo.ru', '79991234567', 'Администратор PayGo', '$2b$12$example_hash_for_admin', 'admin')
ON CONFLICT (email) DO NOTHING;

-- Создание демо-терминала
INSERT INTO terminals (terminal_id, name, location, address, terminal_type, status) VALUES 
('DEMO_001', 'Демо терминал', 'Офис PayGo', 'г. Ростов-на-Дону, ул. Пушкинская, 1', 'payment', 'offline')
ON CONFLICT (terminal_id) DO NOTHING; 