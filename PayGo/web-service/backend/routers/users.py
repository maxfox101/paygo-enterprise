from fastapi import APIRouter, HTTPException, Depends, status, Query
from sqlalchemy.orm import Session
from typing import List, Optional
from sqlalchemy import func

from models.user import User, UserUpdate, UserResponse, UserBiometry
from models.card import Card, CardResponse
from models.transaction import Transaction, TransactionResponse
from database import get_db
from auth_utils import get_current_user, get_current_admin_user

router = APIRouter()

@router.get("/me", response_model=UserResponse)
async def get_my_profile(current_user: User = Depends(get_current_user)):
    """Получение профиля текущего пользователя"""
    return current_user

@router.put("/me", response_model=UserResponse)
async def update_my_profile(
    user_update: UserUpdate,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """Обновление профиля текущего пользователя"""
    
    # Проверка уникальности email и phone, если они изменяются
    if user_update.email and user_update.email != current_user.email:
        existing_user = db.query(User).filter(User.email == user_update.email, User.id != current_user.id).first()
        if existing_user:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Пользователь с таким email уже существует"
            )
    
    if user_update.phone and user_update.phone != current_user.phone:
        existing_user = db.query(User).filter(User.phone == user_update.phone, User.id != current_user.id).first()
        if existing_user:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Пользователь с таким телефоном уже существует"
            )
    
    # Обновление полей
    update_data = user_update.dict(exclude_unset=True)
    for field, value in update_data.items():
        setattr(current_user, field, value)
    
    db.commit()
    db.refresh(current_user)
    
    return current_user

@router.get("/me/cards", response_model=List[CardResponse])
async def get_my_cards(
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """Получение списка карт текущего пользователя"""
    
    cards = db.query(Card).filter(Card.user_id == current_user.id).all()
    return cards

@router.get("/me/transactions", response_model=List[TransactionResponse])
async def get_my_transactions(
    skip: int = Query(0, ge=0),
    limit: int = Query(50, ge=1, le=100),
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """Получение истории транзакций текущего пользователя"""
    
    transactions = db.query(Transaction).filter(
        Transaction.user_id == current_user.id
    ).order_by(Transaction.created_at.desc()).offset(skip).limit(limit).all()
    
    return transactions

@router.post("/me/biometry")
async def add_biometry_data(
    biometry_data: UserBiometry,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """Добавление биометрических данных пользователя"""
    
    # В реальной системе здесь должна быть логика сохранения биометрических шаблонов
    # в зашифрованном виде или в специализированной БД
    
    # Пока просто возвращаем успешный ответ
    return {"message": "Биометрические данные успешно добавлены"}

@router.delete("/me/biometry/{biometry_type}")
async def remove_biometry_data(
    biometry_type: str,  # "face" или "fingerprint"
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """Удаление биометрических данных пользователя"""
    
    if biometry_type not in ["face", "fingerprint"]:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Неверный тип биометрии"
        )
    
    # Логика удаления биометрических данных
    return {"message": f"Биометрические данные {biometry_type} успешно удалены"}

@router.get("/me/stats")
async def get_my_stats(
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """Получение статистики пользователя"""
    
    # Подсчет статистики
    total_transactions = db.query(Transaction).filter(Transaction.user_id == current_user.id).count()
    successful_transactions = db.query(Transaction).filter(
        Transaction.user_id == current_user.id,
        Transaction.status == "completed"
    ).count()
    
    total_spent = db.query(func.sum(Transaction.amount)).filter(
        Transaction.user_id == current_user.id,
        Transaction.status == "completed"
    ).scalar() or 0.0
    
    total_cards = db.query(Card).filter(Card.user_id == current_user.id).count()
    active_cards = db.query(Card).filter(Card.user_id == current_user.id, Card.is_active == True).count()
    
    return {
        "total_transactions": total_transactions,
        "successful_transactions": successful_transactions,
        "failed_transactions": total_transactions - successful_transactions,
        "total_spent": total_spent,
        "average_transaction": total_spent / max(successful_transactions, 1),
        "total_cards": total_cards,
        "active_cards": active_cards,
        "member_since": current_user.created_at
    }

# Административные эндпоинты для управления пользователями

@router.get("/", response_model=List[UserResponse])
async def get_all_users(
    skip: int = Query(0, ge=0),
    limit: int = Query(100, ge=1, le=1000),
    search: Optional[str] = None,
    current_user: User = Depends(get_current_admin_user),
    db: Session = Depends(get_db)
):
    """Получение списка всех пользователей (только для администраторов)"""
    
    query = db.query(User)
    
    if search:
        query = query.filter(
            (User.full_name.ilike(f"%{search}%")) |
            (User.email.ilike(f"%{search}%")) |
            (User.phone.ilike(f"%{search}%"))
        )
    
    users = query.offset(skip).limit(limit).all()
    return users

@router.get("/{user_id}", response_model=UserResponse)
async def get_user_by_id(
    user_id: int,
    current_user: User = Depends(get_current_admin_user),
    db: Session = Depends(get_db)
):
    """Получение пользователя по ID (только для администраторов)"""
    
    user = db.query(User).filter(User.id == user_id).first()
    if not user:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Пользователь не найден"
        )
    
    return user

@router.put("/{user_id}/status")
async def update_user_status(
    user_id: int,
    is_active: bool,
    current_user: User = Depends(get_current_admin_user),
    db: Session = Depends(get_db)
):
    """Изменение статуса пользователя (активен/неактивен)"""
    
    user = db.query(User).filter(User.id == user_id).first()
    if not user:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Пользователь не найден"
        )
    
    user.is_active = is_active
    db.commit()
    
    status_text = "активирован" if is_active else "деактивирован"
    return {"message": f"Пользователь {status_text}"}

@router.delete("/{user_id}")
async def delete_user(
    user_id: int,
    current_user: User = Depends(get_current_admin_user),
    db: Session = Depends(get_db)
):
    """Удаление пользователя (только для администраторов)"""
    
    if user_id == current_user.id:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Нельзя удалить самого себя"
        )
    
    user = db.query(User).filter(User.id == user_id).first()
    if not user:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Пользователь не найден"
        )
    
    db.delete(user)
    db.commit()
    
    return {"message": "Пользователь успешно удален"} 