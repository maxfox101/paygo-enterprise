from sqlalchemy import Column, Integer, String, Float, DateTime, Boolean, Text, ForeignKey
from sqlalchemy.sql import func
from sqlalchemy.orm import relationship
from pydantic import BaseModel, validator
from typing import Optional, Dict
from datetime import datetime
from decimal import Decimal
from enum import Enum

from database import Base

# Статусы транзакций
class TransactionStatus(str, Enum):
    PENDING = "pending"
    PROCESSING = "processing"
    COMPLETED = "completed"
    FAILED = "failed"
    CANCELLED = "cancelled"
    REFUNDED = "refunded"

# Типы платежей
class PaymentMethod(str, Enum):
    NFC_CARD = "nfc_card"
    NFC_PHONE = "nfc_phone"
    QR_CODE = "qr_code"
    BIOMETRY_FACE = "biometry_face"
    BIOMETRY_FINGERPRINT = "biometry_fingerprint"

# Банки-эквайеры
class BankAcquirer(str, Enum):
    VTB = "vtb"
    ALFABANK = "alfabank"
    CENTRINVEST = "centrinvest"
    SBP = "sbp"

# SQLAlchemy модель
class Transaction(Base):
    __tablename__ = "transactions"
    
    id = Column(Integer, primary_key=True, index=True)
    transaction_id = Column(String, unique=True, index=True, nullable=False)
    
    # Связи
    terminal_id = Column(Integer, ForeignKey("terminals.id"), nullable=False)
    user_id = Column(Integer, ForeignKey("users.id"), nullable=True)  # Может быть анонимная транзакция
    
    # Основные данные
    amount = Column(Float, nullable=False)
    currency = Column(String, default="RUB", nullable=False)
    description = Column(Text, nullable=True)
    
    # Статус и метод оплаты
    status = Column(String, default=TransactionStatus.PENDING)
    payment_method = Column(String, nullable=False)
    bank_acquirer = Column(String, nullable=True)
    
    # Данные от банка
    bank_transaction_id = Column(String, nullable=True)
    bank_response = Column(Text, nullable=True)  # JSON ответ от банка
    
    # Дополнительная информация
    card_mask = Column(String, nullable=True)  # Замаскированный номер карты
    receipt_number = Column(String, nullable=True)
    fiscal_data = Column(Text, nullable=True)  # Данные фискального чека
    
    # Временные метки
    created_at = Column(DateTime, server_default=func.now())
    processed_at = Column(DateTime, nullable=True)
    completed_at = Column(DateTime, nullable=True)
    
    # Отношения
    terminal = relationship("Terminal", back_populates="transactions")
    user = relationship("User", back_populates="transactions")

# Pydantic схемы
class TransactionBase(BaseModel):
    amount: float
    currency: str = "RUB"
    description: Optional[str] = None
    payment_method: PaymentMethod
    
    @validator('amount')
    def validate_amount(cls, v):
        if v <= 0:
            raise ValueError('Сумма должна быть больше нуля')
        if v > 1000000:  # Максимум 1 миллион рублей
            raise ValueError('Сумма превышает максимально допустимую')
        # Округляем до копеек
        return round(float(v), 2)

class TransactionCreate(TransactionBase):
    terminal_id: int
    user_id: Optional[int] = None
    
class TransactionUpdate(BaseModel):
    status: Optional[TransactionStatus] = None
    bank_transaction_id: Optional[str] = None
    bank_response: Optional[str] = None
    card_mask: Optional[str] = None
    receipt_number: Optional[str] = None
    fiscal_data: Optional[str] = None

class TransactionInDB(TransactionBase):
    id: int
    transaction_id: str
    terminal_id: int
    user_id: Optional[int]
    status: TransactionStatus
    bank_acquirer: Optional[BankAcquirer]
    bank_transaction_id: Optional[str]
    bank_response: Optional[str]
    card_mask: Optional[str]
    receipt_number: Optional[str]
    fiscal_data: Optional[str]
    created_at: datetime
    processed_at: Optional[datetime]
    completed_at: Optional[datetime]
    
    class Config:
        orm_mode = True

class TransactionResponse(TransactionBase):
    id: int
    transaction_id: str
    status: TransactionStatus
    card_mask: Optional[str]
    receipt_number: Optional[str]
    created_at: datetime
    completed_at: Optional[datetime]
    
    class Config:
        orm_mode = True

# Схема для начала платежа с терминала
class PaymentRequest(BaseModel):
    terminal_id: str
    amount: float
    payment_method: PaymentMethod
    user_phone: Optional[str] = None  # Для привязки к пользователю
    description: Optional[str] = None
    
    @validator('amount')
    def validate_amount(cls, v):
        return round(float(v), 2)

# Ответ на запрос платежа
class PaymentResponse(BaseModel):
    transaction_id: str
    status: TransactionStatus
    qr_code: Optional[str] = None  # Для QR платежей
    nfc_data: Optional[str] = None  # Для NFC платежей
    biometry_challenge: Optional[str] = None  # Для биометрии
    expires_at: datetime

# Подтверждение платежа
class PaymentConfirmation(BaseModel):
    transaction_id: str
    payment_data: Dict  # Данные от устройства (карта, биометрия и т.д.)
    terminal_signature: str  # Подпись терминала

# Статистика по транзакциям
class TransactionStats(BaseModel):
    period_start: datetime
    period_end: datetime
    total_count: int
    successful_count: int
    failed_count: int
    total_amount: float
    average_amount: float
    by_payment_method: Dict[str, int]
    by_hour: Dict[int, int]

# Чек транзакции
class TransactionReceipt(BaseModel):
    transaction_id: str
    receipt_number: str
    amount: float
    currency: str
    payment_method: str
    card_mask: Optional[str]
    terminal_location: str
    timestamp: datetime
    fiscal_data: Optional[Dict] 