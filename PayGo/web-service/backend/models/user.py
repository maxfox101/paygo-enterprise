from sqlalchemy import Column, Integer, String, Boolean, DateTime, Text
from sqlalchemy.sql import func
from pydantic import BaseModel, EmailStr, validator
from typing import Optional, List
from datetime import datetime
from enum import Enum

from database import Base

# Роли пользователей
class UserRole(str, Enum):
    USER = "user"
    ADMIN = "admin"
    OPERATOR = "operator"

# SQLAlchemy модель
class User(Base):
    __tablename__ = "users"
    
    id = Column(Integer, primary_key=True, index=True)
    email = Column(String, unique=True, index=True, nullable=False)
    phone = Column(String, unique=True, index=True, nullable=False)
    full_name = Column(String, nullable=False)
    hashed_password = Column(String, nullable=False)
    role = Column(String, default=UserRole.USER, nullable=False)
    is_active = Column(Boolean, default=True)
    is_verified = Column(Boolean, default=False)
    avatar_url = Column(String, nullable=True)
    created_at = Column(DateTime, server_default=func.now())
    updated_at = Column(DateTime, server_default=func.now(), onupdate=func.now())
    last_login = Column(DateTime, nullable=True)

# Pydantic схемы
class UserBase(BaseModel):
    email: EmailStr
    phone: str
    full_name: str
    role: UserRole = UserRole.USER
    is_active: bool = True

class UserCreate(UserBase):
    password: str
    
    @validator('password')
    def validate_password(cls, v):
        if len(v) < 8:
            raise ValueError('Пароль должен содержать минимум 8 символов')
        if not any(c.isdigit() for c in v):
            raise ValueError('Пароль должен содержать цифры')
        if not any(c.isalpha() for c in v):
            raise ValueError('Пароль должен содержать буквы')
        return v
    
    @validator('phone')
    def validate_phone(cls, v):
        # Простая валидация российского номера
        v = v.replace('+', '').replace(' ', '').replace('-', '').replace('(', '').replace(')', '')
        if not v.startswith('7') or len(v) != 11:
            raise ValueError('Неверный формат российского номера телефона')
        return v

class UserUpdate(BaseModel):
    email: Optional[EmailStr] = None
    phone: Optional[str] = None
    full_name: Optional[str] = None
    avatar_url: Optional[str] = None

class UserInDB(UserBase):
    id: int
    hashed_password: str
    is_verified: bool
    created_at: datetime
    updated_at: datetime
    last_login: Optional[datetime]
    
    class Config:
        orm_mode = True

class UserResponse(UserBase):
    id: int
    is_verified: bool
    avatar_url: Optional[str]
    created_at: datetime
    last_login: Optional[datetime]
    
    class Config:
        orm_mode = True

# Схемы для аутентификации
class UserLogin(BaseModel):
    email: EmailStr
    password: str

class Token(BaseModel):
    access_token: str
    refresh_token: str
    token_type: str = "bearer"

class TokenData(BaseModel):
    user_id: Optional[int] = None
    
# Биометрические данные пользователя
class UserBiometry(BaseModel):
    user_id: int
    face_template: Optional[str] = None  # Base64 encoded
    fingerprint_template: Optional[str] = None  # Base64 encoded
    is_face_enabled: bool = False
    is_fingerprint_enabled: bool = False 