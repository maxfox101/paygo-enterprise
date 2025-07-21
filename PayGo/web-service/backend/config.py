from pydantic_settings import BaseSettings
from typing import List
import os

class Settings(BaseSettings):
    # Основные настройки приложения
    APP_NAME: str = "PayGo API"
    VERSION: str = "1.0.0"
    DEBUG: bool = False
    
    # API настройки
    API_HOST: str = "0.0.0.0"
    API_PORT: int = 8000
    
    # База данных
    DATABASE_URL: str = "postgresql://paygo_user:paygo_password@database:5432/paygo"
    
    # Redis
    REDIS_URL: str = "redis://redis:6379"
    
    # Безопасность
    SECRET_KEY: str = "your-secret-key-change-in-production"
    JWT_ALGORITHM: str = "HS256"
    ACCESS_TOKEN_EXPIRE_MINUTES: int = 30
    REFRESH_TOKEN_EXPIRE_DAYS: int = 7
    
    # CORS и хосты
    ALLOWED_HOSTS: List[str] = ["*"]
    
    # Банковские API
    VTB_API_URL: str = "https://api.vtb.ru/acquiring"
    VTB_MERCHANT_ID: str = "VTB_MERCHANT_ID"
    VTB_API_KEY: str = ""
    
    ALFA_API_URL: str = "https://api.alfabank.ru/acquiring"
    ALFA_MERCHANT_ID: str = "ALFA_MERCHANT_ID"
    ALFA_API_KEY: str = ""
    
    CENTRINVEST_API_URL: str = "https://api.centrinvest.ru/acquiring"
    CENTRINVEST_MERCHANT_ID: str = "CI_MERCHANT_ID"
    CENTRINVEST_API_KEY: str = ""
    
    # СБП
    SBP_API_URL: str = "https://api.sbp.ru"
    SBP_MERCHANT_ID: str = "SBP_MERCHANT_ID"
    SBP_API_KEY: str = ""
    
    # Файловое хранилище
    UPLOAD_DIR: str = "/app/uploads"
    MAX_FILE_SIZE: int = 10 * 1024 * 1024  # 10MB
    
    # Email настройки (для уведомлений)
    SMTP_HOST: str = ""
    SMTP_PORT: int = 587
    SMTP_USER: str = ""
    SMTP_PASSWORD: str = ""
    
    # Логирование
    LOG_LEVEL: str = "INFO"
    
    # Лимиты
    RATE_LIMIT_PER_MINUTE: int = 100
    
    class Config:
        env_file = ".env"
        case_sensitive = True

# Создание экземпляра настроек
settings = Settings() 