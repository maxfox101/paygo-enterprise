from fastapi import APIRouter, HTTPException, Depends, status, Query
from sqlalchemy.orm import Session
from typing import List, Optional
from datetime import datetime, timedelta
import uuid

from models.transaction import (
    Transaction, TransactionCreate, TransactionUpdate, TransactionResponse,
    PaymentRequest, PaymentResponse, PaymentConfirmation, TransactionStats,
    TransactionReceipt, TransactionStatus, PaymentMethod
)
from models.terminal import Terminal
from models.user import User
from database import get_db
from auth_utils import get_current_user, get_current_admin_user
from payment_processor import process_payment
from sqlalchemy import func
import json

router = APIRouter()

@router.post("/payment-request", response_model=PaymentResponse)
async def create_payment_request(
    payment_data: PaymentRequest,
    db: Session = Depends(get_db)
):
    """Создание запроса на платеж от терминала"""
    
    # Проверка существования терминала
    terminal = db.query(Terminal).filter(Terminal.terminal_id == payment_data.terminal_id).first()
    if not terminal:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Терминал не найден"
        )
    
    # Проверка статуса терминала
    if terminal.status not in ["online", "maintenance"]:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Терминал недоступен"
        )
    
    # Поиск пользователя по телефону (если указан)
    user_id = None
    if payment_data.user_phone:
        user = db.query(User).filter(User.phone == payment_data.user_phone).first()
        if user:
            user_id = user.id
    
    # Генерация уникального ID транзакции
    transaction_id = f"TXN_{terminal.terminal_id}_{int(datetime.utcnow().timestamp())}_{uuid.uuid4().hex[:8]}"
    
    # Создание транзакции
    db_transaction = Transaction(
        transaction_id=transaction_id,
        terminal_id=terminal.id,
        user_id=user_id,
        amount=payment_data.amount,
        description=payment_data.description,
        payment_method=payment_data.payment_method,
        status=TransactionStatus.PENDING
    )
    
    db.add(db_transaction)
    db.commit()
    db.refresh(db_transaction)
    
    # Подготовка ответа в зависимости от метода оплаты
    expires_at = datetime.utcnow() + timedelta(minutes=5)  # 5 минут на оплату
    
    response_data = {
        "transaction_id": transaction_id,
        "status": TransactionStatus.PENDING,
        "expires_at": expires_at
    }
    
    # Дополнительные данные для конкретных методов оплаты
    if payment_data.payment_method == PaymentMethod.QR_CODE:
        # Генерация QR кода для СБП
        qr_data = f"https://qr.nspk.ru/AD10006M8A01{payment_data.amount:012.0f}S{terminal.terminal_id}I{transaction_id}"
        response_data["qr_code"] = qr_data
    
    elif payment_data.payment_method in [PaymentMethod.BIOMETRY_FACE, PaymentMethod.BIOMETRY_FINGERPRINT]:
        # Генерация challenge для биометрии
        response_data["biometry_challenge"] = f"CHALLENGE_{transaction_id}_{uuid.uuid4().hex[:8]}"
    
    return PaymentResponse(**response_data)

@router.post("/payment-confirm")
async def confirm_payment(
    confirmation: PaymentConfirmation,
    db: Session = Depends(get_db)
):
    """Подтверждение платежа от терминала"""
    
    # Поиск транзакции
    transaction = db.query(Transaction).filter(Transaction.transaction_id == confirmation.transaction_id).first()
    if not transaction:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Транзакция не найдена"
        )
    
    # Проверка статуса транзакции
    if transaction.status != TransactionStatus.PENDING:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Транзакция уже обработана"
        )
    
    # Проверка подписи терминала (в реальной системе)
    # verify_terminal_signature(confirmation.terminal_signature, transaction)
    
    try:
        # Изменение статуса на обработку
        transaction.status = TransactionStatus.PROCESSING
        transaction.processed_at = datetime.utcnow()
        db.commit()
        
        # Обработка платежа через банк/СБП
        payment_result = await process_payment(transaction, confirmation.payment_data)
        
        if payment_result.success:
            # Успешный платеж
            transaction.status = TransactionStatus.COMPLETED
            transaction.completed_at = datetime.utcnow()
            transaction.bank_transaction_id = payment_result.bank_transaction_id
            transaction.bank_response = payment_result.bank_response
            transaction.card_mask = payment_result.card_mask
            transaction.receipt_number = payment_result.receipt_number
            
            # Обновление статистики терминала
            terminal = db.query(Terminal).filter(Terminal.id == transaction.terminal_id).first()
            terminal.total_transactions += 1
            terminal.total_amount += transaction.amount
            
        else:
            # Неудачный платеж
            transaction.status = TransactionStatus.FAILED
            transaction.bank_response = payment_result.error_message
        
        db.commit()
        
        return {
            "transaction_id": transaction.transaction_id,
            "status": transaction.status,
            "bank_transaction_id": transaction.bank_transaction_id,
            "receipt_number": transaction.receipt_number
        }
        
    except Exception as e:
        # Ошибка при обработке
        transaction.status = TransactionStatus.FAILED
        transaction.bank_response = str(e)
        db.commit()
        
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Ошибка при обработке платежа"
        )

@router.get("/", response_model=List[TransactionResponse])
async def get_transactions(
    skip: int = Query(0, ge=0),
    limit: int = Query(100, ge=1, le=1000),
    status: Optional[TransactionStatus] = None,
    terminal_id: Optional[str] = None,
    date_from: Optional[datetime] = None,
    date_to: Optional[datetime] = None,
    current_user: User = Depends(get_current_admin_user),
    db: Session = Depends(get_db)
):
    """Получение списка транзакций (только для администраторов)"""
    
    query = db.query(Transaction)
    
    if status:
        query = query.filter(Transaction.status == status)
    
    if terminal_id:
        terminal = db.query(Terminal).filter(Terminal.terminal_id == terminal_id).first()
        if terminal:
            query = query.filter(Transaction.terminal_id == terminal.id)
    
    if date_from:
        query = query.filter(Transaction.created_at >= date_from)
    
    if date_to:
        query = query.filter(Transaction.created_at <= date_to)
    
    transactions = query.order_by(Transaction.created_at.desc()).offset(skip).limit(limit).all()
    return transactions

@router.get("/{transaction_id}", response_model=TransactionResponse)
async def get_transaction(
    transaction_id: str,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """Получение информации о транзакции"""
    
    transaction = db.query(Transaction).filter(Transaction.transaction_id == transaction_id).first()
    if not transaction:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Транзакция не найдена"
        )
    
    # Проверка прав доступа
    if current_user.role not in ["admin", "operator"]:
        if not transaction.user_id or transaction.user_id != current_user.id:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="Недостаточно прав для просмотра транзакции"
            )
    
    return transaction

@router.get("/{transaction_id}/receipt", response_model=TransactionReceipt)
async def get_transaction_receipt(
    transaction_id: str,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """Получение чека транзакции"""
    
    transaction = db.query(Transaction).filter(Transaction.transaction_id == transaction_id).first()
    if not transaction:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Транзакция не найдена"
        )
    
    # Проверка прав доступа
    if current_user.role not in ["admin", "operator"]:
        if not transaction.user_id or transaction.user_id != current_user.id:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="Недостаточно прав для просмотра чека"
            )
    
    # Проверка статуса транзакции
    if transaction.status != TransactionStatus.COMPLETED:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Чек доступен только для завершенных транзакций"
        )
    
    terminal = db.query(Terminal).filter(Terminal.id == transaction.terminal_id).first()
    
    fiscal_data = None
    if transaction.fiscal_data:
        fiscal_data = json.loads(transaction.fiscal_data)
    
    receipt = TransactionReceipt(
        transaction_id=transaction.transaction_id,
        receipt_number=transaction.receipt_number or "N/A",
        amount=transaction.amount,
        currency=transaction.currency,
        payment_method=transaction.payment_method,
        card_mask=transaction.card_mask,
        terminal_location=terminal.location if terminal else "Неизвестно",
        timestamp=transaction.completed_at or transaction.created_at,
        fiscal_data=fiscal_data
    )
    
    return receipt

@router.post("/{transaction_id}/refund")
async def refund_transaction(
    transaction_id: str,
    reason: Optional[str] = None,
    current_user: User = Depends(get_current_admin_user),
    db: Session = Depends(get_db)
):
    """Возврат средств по транзакции"""
    
    transaction = db.query(Transaction).filter(Transaction.transaction_id == transaction_id).first()
    if not transaction:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Транзакция не найдена"
        )
    
    if transaction.status != TransactionStatus.COMPLETED:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Возврат возможен только для завершенных транзакций"
        )
    
    # Проверка времени (обычно возврат доступен в течение определенного периода)
    days_since_transaction = (datetime.utcnow() - transaction.completed_at).days
    if days_since_transaction > 90:  # 90 дней
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Срок для возврата истек"
        )
    
    try:
        # Обработка возврата через банк
        # refund_result = await process_refund(transaction)
        
        transaction.status = TransactionStatus.REFUNDED
        db.commit()
        
        return {"message": "Возврат успешно выполнен"}
        
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Ошибка при выполнении возврата"
        )

@router.get("/stats/summary", response_model=TransactionStats)
async def get_transactions_stats(
    days: int = Query(30, ge=1, le=365),
    terminal_id: Optional[str] = None,
    current_user: User = Depends(get_current_admin_user),
    db: Session = Depends(get_db)
):
    """Получение статистики по транзакциям"""
    
    period_end = datetime.utcnow()
    period_start = period_end - timedelta(days=days)
    
    query = db.query(Transaction).filter(
        Transaction.created_at >= period_start,
        Transaction.created_at <= period_end
    )
    
    if terminal_id:
        terminal = db.query(Terminal).filter(Terminal.terminal_id == terminal_id).first()
        if terminal:
            query = query.filter(Transaction.terminal_id == terminal.id)
    
    # Подсчет статистики
    total_count = query.count()
    successful_count = query.filter(Transaction.status == TransactionStatus.COMPLETED).count()
    failed_count = query.filter(Transaction.status == TransactionStatus.FAILED).count()
    
    total_amount = query.filter(Transaction.status == TransactionStatus.COMPLETED).with_entities(func.sum(Transaction.amount)).scalar() or 0.0
    average_amount = total_amount / max(successful_count, 1)
    
    # Статистика по методам оплаты
    payment_methods_stats = {}
    for method in PaymentMethod:
        count = query.filter(Transaction.payment_method == method.value).count()
        if count > 0:
            payment_methods_stats[method.value] = count
    
    # Статистика по часам (последние 24 часа)
    by_hour = {}
    for hour in range(24):
        start_hour = datetime.utcnow().replace(minute=0, second=0, microsecond=0) - timedelta(hours=23-hour)
        end_hour = start_hour + timedelta(hours=1)
        count = query.filter(
            Transaction.created_at >= start_hour,
            Transaction.created_at < end_hour
        ).count()
        by_hour[hour] = count
    
    stats = TransactionStats(
        period_start=period_start,
        period_end=period_end,
        total_count=total_count,
        successful_count=successful_count,
        failed_count=failed_count,
        total_amount=total_amount,
        average_amount=average_amount,
        by_payment_method=payment_methods_stats,
        by_hour=by_hour
    )
    
    return stats 