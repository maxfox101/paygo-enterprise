from sqlalchemy import Column, Integer, String, Boolean, DateTime, ForeignKey
from sqlalchemy.sql import func
from sqlalchemy.orm import relationship
from pydantic import BaseModel, validator
from typing import Optional, List
from datetime import datetime
from enum import Enum

from database import Base

# Типы карт
class CardType(str, Enum):
    DEBIT = "debit"
    CREDIT = "credit"
    PREPAID = "prepaid"

# Платежные системы
class PaymentSystem(str, Enum):
    VISA = "visa"
    MASTERCARD = "mastercard"
    MIR = "mir"
    UNIONPAY = "unionpay"

# Банки-эмитенты
class BankIssuer(str, Enum):
    SBERBANK = "sberbank"
    VTB = "vtb"
    ALFABANK = "alfabank"
    GAZPROMBANK = "gazprombank"
    TINKOFF = "tinkoff"
    CENTRINVEST = "centrinvest"
    OTHER = "other"

# SQLAlchemy модель
class Card(Base):
    __tablename__ = "cards"
    
    id = Column(Integer, primary_key=True, index=True)
    user_id = Column(Integer, ForeignKey("users.id"), nullable=False)
    
    # Основные данные карты
    card_token = Column(String, unique=True, index=True, nullable=False)  # Токен вместо номера
    card_mask = Column(String, nullable=False)  # Замаскированный номер (например: **** **** **** 1234)
    card_holder_name = Column(String, nullable=False)
    
    # Тип и система
    card_type = Column(String, nullable=False)
    payment_system = Column(String, nullable=False)
    bank_issuer = Column(String, nullable=False)
    
    # Статус карты
    is_active = Column(Boolean, default=True)
    is_primary = Column(Boolean, default=False)  # Основная карта пользователя
    is_verified = Column(Boolean, default=False)
    
    # Дополнительная информация
    expiry_month = Column(Integer, nullable=True)
    expiry_year = Column(Integer, nullable=True)
    
    # Временные метки
    created_at = Column(DateTime, server_default=func.now())
    updated_at = Column(DateTime, server_default=func.now(), onupdate=func.now())
    last_used = Column(DateTime, nullable=True)
    
    # Отношения
    user = relationship("User", back_populates="cards")

# Pydantic схемы
class CardBase(BaseModel):
    card_holder_name: str
    card_type: CardType
    payment_system: PaymentSystem
    bank_issuer: BankIssuer
    
    @validator('card_holder_name')
    def validate_card_holder_name(cls, v):
        v = v.strip().upper()
        if len(v) < 2:
            raise ValueError('Имя держателя карты слишком короткое')
        if len(v) > 50:
            raise ValueError('Имя держателя карты слишком длинное')
        # Проверка на латинские буквы и пробелы
        if not all(c.isalpha() or c.isspace() for c in v):
            raise ValueError('Имя держателя должно содержать только латинские буквы')
        return v

class CardCreate(CardBase):
    card_number: str  # Полный номер карты (будет токенизирован)
    expiry_month: int
    expiry_year: int
    cvv: str  # CVV код (не сохраняется, используется только для верификации)
    
    @validator('card_number')
    def validate_card_number(cls, v):
        # Удаляем пробелы и дефисы
        v = v.replace(' ', '').replace('-', '')
        if not v.isdigit():
            raise ValueError('Номер карты должен содержать только цифры')
        if len(v) < 13 or len(v) > 19:
            raise ValueError('Неверная длина номера карты')
        
        # Проверка по алгоритму Луна
        def luhn_checksum(card_num):
            def digits_of(number):
                return [int(d) for d in str(number)]
            digits = digits_of(card_num)
            odd_digits = digits[-1::-2]
            even_digits = digits[-2::-2]
            checksum = sum(odd_digits)
            for d in even_digits:
                checksum += sum(digits_of(d*2))
            return checksum % 10
        
        if luhn_checksum(v) != 0:
            raise ValueError('Неверный номер карты')
            
        return v
    
    @validator('expiry_month')
    def validate_expiry_month(cls, v):
        if v < 1 or v > 12:
            raise ValueError('Неверный месяц истечения срока действия')
        return v
    
    @validator('expiry_year')
    def validate_expiry_year(cls, v):
        current_year = datetime.now().year
        if v < current_year or v > current_year + 20:
            raise ValueError('Неверный год истечения срока действия')
        return v
    
    @validator('cvv')
    def validate_cvv(cls, v):
        if not v.isdigit() or len(v) not in [3, 4]:
            raise ValueError('Неверный CVV код')
        return v

class CardUpdate(BaseModel):
    card_holder_name: Optional[str] = None
    is_active: Optional[bool] = None
    is_primary: Optional[bool] = None

class CardInDB(CardBase):
    id: int
    user_id: int
    card_token: str
    card_mask: str
    is_active: bool
    is_primary: bool
    is_verified: bool
    expiry_month: Optional[int]
    expiry_year: Optional[int]
    created_at: datetime
    updated_at: datetime
    last_used: Optional[datetime]
    
    class Config:
        orm_mode = True

class CardResponse(CardBase):
    id: int
    card_mask: str
    is_active: bool
    is_primary: bool
    is_verified: bool
    expiry_month: Optional[int]
    expiry_year: Optional[int]
    created_at: datetime
    last_used: Optional[datetime]
    
    class Config:
        orm_mode = True

# Схема для привязки карты через банк
class CardBindingRequest(BaseModel):
    bank_code: str  # Код банка для редиректа
    return_url: str  # URL для возврата после привязки

class CardBindingResponse(BaseModel):
    binding_id: str
    redirect_url: str  # URL банка для ввода данных карты
    expires_at: datetime

# Верификация карты малой суммой
class CardVerification(BaseModel):
    card_id: int
    verification_amount: float  # Сумма для верификации (обычно 1 руб)

# Статистика по картам
class CardStats(BaseModel):
    user_id: int
    total_cards: int
    active_cards: int
    verified_cards: int
    transactions_count: int
    total_spent: float
    by_payment_system: dict
    by_bank: dict 