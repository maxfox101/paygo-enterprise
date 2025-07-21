from sqlalchemy import Column, Integer, String, Boolean, DateTime, Text, Float, JSON
from sqlalchemy.sql import func
from pydantic import BaseModel, validator
from typing import Optional, Dict, List
from datetime import datetime
from enum import Enum

from database import Base

# Статусы терминала
class TerminalStatus(str, Enum):
    ONLINE = "online"
    OFFLINE = "offline"
    MAINTENANCE = "maintenance"
    ERROR = "error"
    BLOCKED = "blocked"

# Типы терминалов
class TerminalType(str, Enum):
    PAYMENT = "payment"
    SELF_SERVICE = "self_service"
    KIOSK = "kiosk"

# SQLAlchemy модель
class Terminal(Base):
    __tablename__ = "terminals"
    
    id = Column(Integer, primary_key=True, index=True)
    terminal_id = Column(String, unique=True, index=True, nullable=False)  # Уникальный ID терминала
    name = Column(String, nullable=False)
    location = Column(String, nullable=False)
    address = Column(Text, nullable=True)
    terminal_type = Column(String, default=TerminalType.PAYMENT)
    status = Column(String, default=TerminalStatus.OFFLINE)
    
    # Технические характеристики
    hardware_info = Column(JSON, nullable=True)  # Информация о железе
    software_version = Column(String, nullable=True)
    last_update = Column(DateTime, nullable=True)
    
    # Сетевые настройки
    ip_address = Column(String, nullable=True)
    mac_address = Column(String, nullable=True)
    
    # Статистика
    total_transactions = Column(Integer, default=0)
    total_amount = Column(Float, default=0.0)
    
    # Настройки
    config = Column(JSON, nullable=True)  # Конфигурация терминала
    
    # Временные метки
    created_at = Column(DateTime, server_default=func.now())
    updated_at = Column(DateTime, server_default=func.now(), onupdate=func.now())
    last_heartbeat = Column(DateTime, nullable=True)

# Pydantic схемы
class TerminalBase(BaseModel):
    name: str
    location: str
    address: Optional[str] = None
    terminal_type: TerminalType = TerminalType.PAYMENT

class TerminalCreate(TerminalBase):
    terminal_id: str
    
    @validator('terminal_id')
    def validate_terminal_id(cls, v):
        if len(v) < 3 or len(v) > 50:
            raise ValueError('ID терминала должен быть от 3 до 50 символов')
        if not v.replace('_', '').replace('-', '').isalnum():
            raise ValueError('ID терминала может содержать только буквы, цифры, дефисы и подчеркивания')
        return v.upper()

class TerminalUpdate(BaseModel):
    name: Optional[str] = None
    location: Optional[str] = None
    address: Optional[str] = None
    status: Optional[TerminalStatus] = None
    software_version: Optional[str] = None
    config: Optional[Dict] = None

class TerminalInDB(TerminalBase):
    id: int
    terminal_id: str
    status: TerminalStatus
    hardware_info: Optional[Dict]
    software_version: Optional[str]
    last_update: Optional[datetime]
    ip_address: Optional[str]
    mac_address: Optional[str]
    total_transactions: int
    total_amount: float
    config: Optional[Dict]
    created_at: datetime
    updated_at: datetime
    last_heartbeat: Optional[datetime]
    
    class Config:
        orm_mode = True

class TerminalResponse(TerminalBase):
    id: int
    terminal_id: str
    status: TerminalStatus
    software_version: Optional[str]
    total_transactions: int
    total_amount: float
    created_at: datetime
    last_heartbeat: Optional[datetime]
    
    class Config:
        orm_mode = True

# Heartbeat от терминала
class TerminalHeartbeat(BaseModel):
    terminal_id: str
    status: TerminalStatus
    ip_address: Optional[str] = None
    hardware_info: Optional[Dict] = None
    current_transaction_count: Optional[int] = None
    errors: Optional[List[str]] = None

# Конфигурация терминала
class TerminalConfig(BaseModel):
    payment_methods: List[str] = ["nfc", "qr", "biometry"]
    biometry_settings: Dict = {
        "face_recognition": True,
        "fingerprint": True,
        "liveness_detection": True
    }
    timeout_settings: Dict = {
        "idle_timeout": 60,
        "transaction_timeout": 180
    }
    display_settings: Dict = {
        "language": "ru",
        "theme": "light",
        "brightness": 80
    }
    limits: Dict = {
        "min_amount": 1.0,
        "max_amount": 100000.0,
        "daily_limit": 1000000.0
    }

# Статистика терминала
class TerminalStats(BaseModel):
    terminal_id: str
    period_start: datetime
    period_end: datetime
    transactions_count: int
    successful_transactions: int
    failed_transactions: int
    total_amount: float
    average_amount: float
    uptime_percentage: float
    error_count: int 