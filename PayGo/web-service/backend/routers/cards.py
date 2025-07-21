from fastapi import APIRouter, HTTPException, Depends, status, Query
from sqlalchemy.orm import Session
from typing import List, Optional
import uuid
import hashlib
from datetime import datetime, timedelta
from sqlalchemy import func

from models.card import (
    Card, CardCreate, CardUpdate, CardResponse, CardStats,
    CardBindingRequest, CardBindingResponse, CardVerification
)
from database import get_db
from auth_utils import get_current_user, get_current_admin_user
from models.user import User
from card_tokenizer import tokenize_card, generate_card_mask

router = APIRouter()

@router.get("/", response_model=List[CardResponse])
async def get_my_cards(
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """Получение списка карт текущего пользователя"""
    
    cards = db.query(Card).filter(Card.user_id == current_user.id).order_by(Card.created_at.desc()).all()
    return cards

@router.post("/", response_model=CardResponse, status_code=status.HTTP_201_CREATED)
async def add_card(
    card_data: CardCreate,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """Добавление новой карты"""
    
    try:
        # Токенизация номера карты (в реальной системе через PCI DSS сервис)
        card_token = tokenize_card(card_data.card_number)
        
        # Проверка, что карта не добавлена ранее
        existing_card = db.query(Card).filter(Card.card_token == card_token).first()
        if existing_card:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Эта карта уже добавлена"
            )
        
        # Генерация маски карты
        card_mask = generate_card_mask(card_data.card_number)
        
        # Проверка CVV через банк (в реальной системе)
        # bank_verification = verify_card_with_bank(card_data)
        # if not bank_verification.success:
        #     raise HTTPException(status_code=400, detail="Карта не прошла верификацию")
        
        # Определение, будет ли эта карта основной
        is_primary = db.query(Card).filter(Card.user_id == current_user.id).count() == 0
        
        # Создание записи карты
        db_card = Card(
            user_id=current_user.id,
            card_token=card_token,
            card_mask=card_mask,
            card_holder_name=card_data.card_holder_name,
            card_type=card_data.card_type,
            payment_system=card_data.payment_system,
            bank_issuer=card_data.bank_issuer,
            is_primary=is_primary,
            expiry_month=card_data.expiry_month,
            expiry_year=card_data.expiry_year
        )
        
        db.add(db_card)
        db.commit()
        db.refresh(db_card)
        
        return db_card
        
    except ValueError as e:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=str(e)
        )
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Ошибка при добавлении карты"
        )

@router.get("/{card_id}", response_model=CardResponse)
async def get_card(
    card_id: int,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """Получение информации о карте"""
    
    card = db.query(Card).filter(Card.id == card_id).first()
    if not card:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Карта не найдена"
        )
    
    # Проверка прав доступа
    if current_user.role not in ["admin", "operator"]:
        if card.user_id != current_user.id:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="Недостаточно прав для просмотра карты"
            )
    
    return card

@router.put("/{card_id}", response_model=CardResponse)
async def update_card(
    card_id: int,
    card_update: CardUpdate,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """Обновление информации о карте"""
    
    card = db.query(Card).filter(Card.id == card_id).first()
    if not card:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Карта не найдена"
        )
    
    # Проверка прав доступа
    if card.user_id != current_user.id:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Недостаточно прав для изменения карты"
        )
    
    # Обновление полей
    update_data = card_update.dict(exclude_unset=True)
    
    # Если устанавливаем карту как основную, сбрасываем флаг у других карт
    if update_data.get("is_primary") == True:
        db.query(Card).filter(Card.user_id == current_user.id, Card.id != card_id).update({"is_primary": False})
    
    for field, value in update_data.items():
        setattr(card, field, value)
    
    db.commit()
    db.refresh(card)
    
    return card

@router.delete("/{card_id}")
async def delete_card(
    card_id: int,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """Удаление карты"""
    
    card = db.query(Card).filter(Card.id == card_id).first()
    if not card:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Карта не найдена"
        )
    
    # Проверка прав доступа
    if card.user_id != current_user.id:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Недостаточно прав для удаления карты"
        )
    
    # Если удаляем основную карту, назначаем другую основной
    if card.is_primary:
        other_card = db.query(Card).filter(
            Card.user_id == current_user.id,
            Card.id != card_id,
            Card.is_active == True
        ).first()
        
        if other_card:
            other_card.is_primary = True
    
    db.delete(card)
    db.commit()
    
    return {"message": "Карта успешно удалена"}

@router.post("/{card_id}/set-primary")
async def set_primary_card(
    card_id: int,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """Установка карты как основной"""
    
    card = db.query(Card).filter(Card.id == card_id).first()
    if not card:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Карта не найдена"
        )
    
    # Проверка прав доступа
    if card.user_id != current_user.id:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Недостаточно прав для изменения карты"
        )
    
    if not card.is_active:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Нельзя сделать основной неактивную карту"
        )
    
    # Сброс флага у других карт
    db.query(Card).filter(Card.user_id == current_user.id).update({"is_primary": False})
    
    # Установка флага для выбранной карты
    card.is_primary = True
    db.commit()
    
    return {"message": "Карта установлена как основная"}

@router.post("/{card_id}/verify", response_model=CardVerification)
async def verify_card(
    card_id: int,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """Верификация карты малой суммой"""
    
    card = db.query(Card).filter(Card.id == card_id).first()
    if not card:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Карта не найдена"
        )
    
    # Проверка прав доступа
    if card.user_id != current_user.id:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Недостаточно прав для верификации карты"
        )
    
    if card.is_verified:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Карта уже верифицирована"
        )
    
    # Сумма для верификации (обычно 1 руб.)
    verification_amount = 1.0
    
    try:
        # Создание транзакции верификации (в реальной системе)
        # verification_transaction = create_verification_transaction(card, verification_amount)
        
        verification = CardVerification(
            card_id=card_id,
            verification_amount=verification_amount
        )
        
        return verification
        
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Ошибка при верификации карты"
        )

@router.post("/binding-request", response_model=CardBindingResponse)
async def create_card_binding(
    binding_request: CardBindingRequest,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """Создание запроса на привязку карты через банк"""
    
    try:
        # Генерация уникального ID привязки
        binding_id = str(uuid.uuid4())
        
        # URL банка для ввода данных карты (в реальной системе)
        redirect_url = f"https://secure-{binding_request.bank_code}.ru/card-binding?id={binding_id}&return={binding_request.return_url}"
        
        # Время истечения ссылки
        expires_at = datetime.utcnow() + timedelta(hours=1)
        
        binding_response = CardBindingResponse(
            binding_id=binding_id,
            redirect_url=redirect_url,
            expires_at=expires_at
        )
        
        return binding_response
        
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Ошибка при создании запроса привязки"
        )

@router.get("/stats/my", response_model=CardStats)
async def get_my_card_stats(
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """Получение статистики по картам текущего пользователя"""
    
    # Подсчет карт
    total_cards = db.query(Card).filter(Card.user_id == current_user.id).count()
    active_cards = db.query(Card).filter(Card.user_id == current_user.id, Card.is_active == True).count()
    verified_cards = db.query(Card).filter(Card.user_id == current_user.id, Card.is_verified == True).count()
    
    # Подсчет транзакций
    from models.transaction import Transaction
    transactions_count = db.query(Transaction).filter(Transaction.user_id == current_user.id).count()
    total_spent = db.query(func.sum(Transaction.amount)).filter(
        Transaction.user_id == current_user.id,
        Transaction.status == "completed"
    ).scalar() or 0.0
    
    # Статистика по платежным системам
    payment_systems = db.query(Card.payment_system, func.count(Card.id)).filter(
        Card.user_id == current_user.id
    ).group_by(Card.payment_system).all()
    by_payment_system = {system: count for system, count in payment_systems}
    
    # Статистика по банкам
    banks = db.query(Card.bank_issuer, func.count(Card.id)).filter(
        Card.user_id == current_user.id
    ).group_by(Card.bank_issuer).all()
    by_bank = {bank: count for bank, count in banks}
    
    stats = CardStats(
        user_id=current_user.id,
        total_cards=total_cards,
        active_cards=active_cards,
        verified_cards=verified_cards,
        transactions_count=transactions_count,
        total_spent=total_spent,
        by_payment_system=by_payment_system,
        by_bank=by_bank
    )
    
    return stats

# Административные эндпоинты

@router.get("/admin/all", response_model=List[CardResponse])
async def get_all_cards(
    skip: int = Query(0, ge=0),
    limit: int = Query(100, ge=1, le=1000),
    user_id: Optional[int] = None,
    current_user: User = Depends(get_current_admin_user),
    db: Session = Depends(get_db)
):
    """Получение всех карт (только для администраторов)"""
    
    query = db.query(Card)
    
    if user_id:
        query = query.filter(Card.user_id == user_id)
    
    cards = query.offset(skip).limit(limit).all()
    return cards 