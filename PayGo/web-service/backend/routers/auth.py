from fastapi import APIRouter, HTTPException, Depends, status
from fastapi.security import HTTPBearer
from sqlalchemy.orm import Session
from datetime import datetime, timedelta

from models.user import User, UserCreate, UserLogin, Token, UserResponse
from database import get_db
from auth_utils import (
    create_access_token, 
    create_refresh_token,
    verify_password, 
    hash_password,
    get_current_user
)
from jose import jwt, JWTError
from config import settings

router = APIRouter()
security = HTTPBearer()

@router.post("/register", response_model=UserResponse, status_code=status.HTTP_201_CREATED)
async def register(user_data: UserCreate, db: Session = Depends(get_db)):
    """Регистрация нового пользователя"""
    
    # Проверка существования пользователя
    existing_user = db.query(User).filter(
        (User.email == user_data.email) | (User.phone == user_data.phone)
    ).first()
    
    if existing_user:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Пользователь с таким email или телефоном уже существует"
        )
    
    # Хеширование пароля
    hashed_password = hash_password(user_data.password)
    
    # Создание пользователя
    db_user = User(
        email=user_data.email,
        phone=user_data.phone,
        full_name=user_data.full_name,
        hashed_password=hashed_password,
        role=user_data.role,
        is_active=user_data.is_active
    )
    
    db.add(db_user)
    db.commit()
    db.refresh(db_user)
    
    return db_user

@router.post("/login", response_model=Token)
async def login(user_credentials: UserLogin, db: Session = Depends(get_db)):
    """Вход пользователя в систему"""
    
    # Поиск пользователя
    user = db.query(User).filter(User.email == user_credentials.email).first()
    
    if not user or not verify_password(user_credentials.password, user.hashed_password):
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Неверный email или пароль",
            headers={"WWW-Authenticate": "Bearer"},
        )
    
    if not user.is_active:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Аккаунт деактивирован"
        )
    
    # Создание токенов
    access_token = create_access_token(data={"sub": str(user.id)})
    refresh_token = create_refresh_token(data={"sub": str(user.id)})
    
    # Обновление времени последнего входа
    user.last_login = datetime.utcnow()
    db.commit()
    
    return {
        "access_token": access_token,
        "refresh_token": refresh_token,
        "token_type": "bearer"
    }

@router.post("/refresh", response_model=Token)
async def refresh_token(refresh_token: str, db: Session = Depends(get_db)):
    """Обновление access токена по refresh токену"""
    
    try:
        # Декодирование refresh токена
        payload = jwt.decode(refresh_token, settings.SECRET_KEY, algorithms=[settings.JWT_ALGORITHM])
        user_id: str = payload.get("sub")
        
        if user_id is None:
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="Неверный токен"
            )
            
    except JWTError:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Неверный токен"
        )
    
    # Проверка пользователя
    user = db.query(User).filter(User.id == int(user_id)).first()
    if not user:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Пользователь не найден"
        )
    
    # Создание новых токенов
    new_access_token = create_access_token(data={"sub": user_id})
    new_refresh_token = create_refresh_token(data={"sub": user_id})
    
    return {
        "access_token": new_access_token,
        "refresh_token": new_refresh_token,
        "token_type": "bearer"
    }

@router.post("/logout")
async def logout(current_user: User = Depends(get_current_user)):
    """Выход пользователя из системы"""
    
    # В реальной системе здесь бы добавляли токен в черный список
    # Пока просто возвращаем успешный ответ
    
    return {"message": "Успешный выход из системы"}

@router.get("/me", response_model=UserResponse)
async def get_current_user_info(current_user: User = Depends(get_current_user)):
    """Получение информации о текущем пользователе"""
    return current_user

@router.post("/verify-email")
async def verify_email(token: str, db: Session = Depends(get_db)):
    """Верификация email по токену"""
    
    # Здесь должна быть логика верификации email
    # Пока заглушка
    
    return {"message": "Email успешно подтвержден"}

@router.post("/forgot-password")
async def forgot_password(email: str, db: Session = Depends(get_db)):
    """Запрос восстановления пароля"""
    
    user = db.query(User).filter(User.email == email).first()
    if not user:
        # В целях безопасности не сообщаем, что пользователь не найден
        return {"message": "Если email существует, письмо с инструкциями отправлено"}
    
    # Здесь должна быть логика отправки письма
    # Пока заглушка
    
    return {"message": "Письмо с инструкциями отправлено"}

@router.post("/reset-password")
async def reset_password(token: str, new_password: str, db: Session = Depends(get_db)):
    """Сброс пароля по токену"""
    
    # Здесь должна быть логика проверки токена сброса пароля
    # И обновления пароля пользователя
    # Пока заглушка
    
    return {"message": "Пароль успешно изменен"} 