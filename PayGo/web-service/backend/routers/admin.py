from fastapi import APIRouter, HTTPException, Depends, status, Query
from sqlalchemy.orm import Session
from sqlalchemy import func
from typing import List, Optional, Dict
from datetime import datetime, timedelta

from models.user import User
from models.terminal import Terminal, TerminalStatus
from models.transaction import Transaction, TransactionStatus
from models.card import Card
from database import get_db
from auth_utils import get_current_admin_user

router = APIRouter()

@router.get("/dashboard")
async def get_admin_dashboard(
    current_user: User = Depends(get_current_admin_user),
    db: Session = Depends(get_db)
):
    """Получение данных для административной панели"""
    
    # Общая статистика
    total_users = db.query(User).count()
    active_users = db.query(User).filter(User.is_active == True).count()
    verified_users = db.query(User).filter(User.is_verified == True).count()
    
    total_terminals = db.query(Terminal).count()
    online_terminals = db.query(Terminal).filter(Terminal.status == TerminalStatus.ONLINE).count()
    
    total_transactions = db.query(Transaction).count()
    successful_transactions = db.query(Transaction).filter(Transaction.status == TransactionStatus.COMPLETED).count()
    
    total_cards = db.query(Card).count()
    active_cards = db.query(Card).filter(Card.is_active == True).count()
    
    # Финансовая статистика
    total_amount = db.query(func.sum(Transaction.amount)).filter(
        Transaction.status == TransactionStatus.COMPLETED
    ).scalar() or 0.0
    
    # Статистика за последние 30 дней
    month_ago = datetime.utcnow() - timedelta(days=30)
    monthly_transactions = db.query(Transaction).filter(
        Transaction.created_at >= month_ago,
        Transaction.status == TransactionStatus.COMPLETED
    ).count()
    
    monthly_amount = db.query(func.sum(Transaction.amount)).filter(
        Transaction.created_at >= month_ago,
        Transaction.status == TransactionStatus.COMPLETED
    ).scalar() or 0.0
    
    # Статистика за сегодня
    today_start = datetime.utcnow().replace(hour=0, minute=0, second=0, microsecond=0)
    daily_transactions = db.query(Transaction).filter(
        Transaction.created_at >= today_start,
        Transaction.status == TransactionStatus.COMPLETED
    ).count()
    
    daily_amount = db.query(func.sum(Transaction.amount)).filter(
        Transaction.created_at >= today_start,
        Transaction.status == TransactionStatus.COMPLETED
    ).scalar() or 0.0
    
    return {
        "users": {
            "total": total_users,
            "active": active_users,
            "verified": verified_users
        },
        "terminals": {
            "total": total_terminals,
            "online": online_terminals,
            "offline": total_terminals - online_terminals
        },
        "transactions": {
            "total": total_transactions,
            "successful": successful_transactions,
            "success_rate": successful_transactions / max(total_transactions, 1) * 100
        },
        "cards": {
            "total": total_cards,
            "active": active_cards
        },
        "financial": {
            "total_amount": total_amount,
            "monthly_amount": monthly_amount,
            "daily_amount": daily_amount,
            "monthly_transactions": monthly_transactions,
            "daily_transactions": daily_transactions,
            "average_transaction": total_amount / max(successful_transactions, 1)
        }
    }

@router.get("/analytics/transactions")
async def get_transaction_analytics(
    days: int = Query(30, ge=1, le=365),
    current_user: User = Depends(get_current_admin_user),
    db: Session = Depends(get_db)
):
    """Получение аналитики по транзакциям"""
    
    end_date = datetime.utcnow()
    start_date = end_date - timedelta(days=days)
    
    # Транзакции по дням
    daily_stats = []
    for i in range(days):
        day_start = start_date + timedelta(days=i)
        day_end = day_start + timedelta(days=1)
        
        count = db.query(Transaction).filter(
            Transaction.created_at >= day_start,
            Transaction.created_at < day_end,
            Transaction.status == TransactionStatus.COMPLETED
        ).count()
        
        amount = db.query(func.sum(Transaction.amount)).filter(
            Transaction.created_at >= day_start,
            Transaction.created_at < day_end,
            Transaction.status == TransactionStatus.COMPLETED
        ).scalar() or 0.0
        
        daily_stats.append({
            "date": day_start.date().isoformat(),
            "transactions": count,
            "amount": amount
        })
    
    # Статистика по методам оплаты
    payment_methods = db.query(
        Transaction.payment_method,
        func.count(Transaction.id).label('count'),
        func.sum(Transaction.amount).label('amount')
    ).filter(
        Transaction.created_at >= start_date,
        Transaction.status == TransactionStatus.COMPLETED
    ).group_by(Transaction.payment_method).all()
    
    payment_method_stats = [
        {
            "method": method,
            "transactions": count,
            "amount": amount or 0.0
        }
        for method, count, amount in payment_methods
    ]
    
    # Топ терминалов
    top_terminals = db.query(
        Terminal.terminal_id,
        Terminal.name,
        Terminal.location,
        func.count(Transaction.id).label('transactions'),
        func.sum(Transaction.amount).label('amount')
    ).join(Transaction).filter(
        Transaction.created_at >= start_date,
        Transaction.status == TransactionStatus.COMPLETED
    ).group_by(Terminal.id).order_by(func.sum(Transaction.amount).desc()).limit(10).all()
    
    terminal_stats = [
        {
            "terminal_id": terminal_id,
            "name": name,
            "location": location,
            "transactions": transactions,
            "amount": amount or 0.0
        }
        for terminal_id, name, location, transactions, amount in top_terminals
    ]
    
    return {
        "period": {
            "start_date": start_date.date().isoformat(),
            "end_date": end_date.date().isoformat(),
            "days": days
        },
        "daily_stats": daily_stats,
        "payment_methods": payment_method_stats,
        "top_terminals": terminal_stats
    }

@router.get("/analytics/users")
async def get_user_analytics(
    current_user: User = Depends(get_current_admin_user),
    db: Session = Depends(get_db)
):
    """Получение аналитики по пользователям"""
    
    # Регистрации по дням (последние 30 дней)
    days = 30
    end_date = datetime.utcnow()
    start_date = end_date - timedelta(days=days)
    
    daily_registrations = []
    for i in range(days):
        day_start = start_date + timedelta(days=i)
        day_end = day_start + timedelta(days=1)
        
        count = db.query(User).filter(
            User.created_at >= day_start,
            User.created_at < day_end
        ).count()
        
        daily_registrations.append({
            "date": day_start.date().isoformat(),
            "registrations": count
        })
    
    # Статистика по ролям
    role_stats = db.query(
        User.role,
        func.count(User.id)
    ).group_by(User.role).all()
    
    # Активные пользователи (совершили транзакцию за последние 30 дней)
    active_users = db.query(func.count(func.distinct(Transaction.user_id))).filter(
        Transaction.created_at >= start_date,
        Transaction.user_id.isnot(None)
    ).scalar() or 0
    
    # Статистика по картам пользователей
    card_stats = db.query(
        func.count(Card.id).label('total_cards'),
        func.count(func.distinct(Card.user_id)).label('users_with_cards'),
        func.avg(func.count(Card.id)).label('avg_cards_per_user')
    ).group_by(Card.user_id).subquery()
    
    card_summary = db.query(
        func.sum(card_stats.c.total_cards),
        func.count(card_stats.c.users_with_cards),
        func.avg(card_stats.c.avg_cards_per_user)
    ).first()
    
    return {
        "period": {
            "start_date": start_date.date().isoformat(),
            "end_date": end_date.date().isoformat()
        },
        "daily_registrations": daily_registrations,
        "roles": [{"role": role, "count": count} for role, count in role_stats],
        "activity": {
            "active_users_30d": active_users,
            "total_users": db.query(User).count(),
            "activity_rate": active_users / max(db.query(User).count(), 1) * 100
        },
        "cards": {
            "total_cards": card_summary[0] or 0,
            "users_with_cards": card_summary[1] or 0,
            "avg_cards_per_user": round(card_summary[2] or 0, 2)
        }
    }

@router.get("/system-status")
async def get_system_status(
    current_user: User = Depends(get_current_admin_user),
    db: Session = Depends(get_db)
):
    """Получение статуса системы"""
    
    # Статус терминалов
    terminal_statuses = db.query(
        Terminal.status,
        func.count(Terminal.id)
    ).group_by(Terminal.status).all()
    
    # Проблемные терминалы (не подавали heartbeat более часа)
    hour_ago = datetime.utcnow() - timedelta(hours=1)
    problematic_terminals = db.query(Terminal).filter(
        Terminal.last_heartbeat < hour_ago
    ).all()
    
    # Последние ошибки (неудачные транзакции за последний час)
    recent_errors = db.query(Transaction).filter(
        Transaction.created_at >= hour_ago,
        Transaction.status == TransactionStatus.FAILED
    ).order_by(Transaction.created_at.desc()).limit(10).all()
    
    # Статус базы данных
    try:
        db.execute("SELECT 1")
        database_status = "healthy"
    except:
        database_status = "error"
    
    return {
        "timestamp": datetime.utcnow().isoformat(),
        "database": {
            "status": database_status,
            "connections": "N/A"  # В реальной системе получать из пула соединений
        },
        "terminals": {
            "statuses": [{"status": status, "count": count} for status, count in terminal_statuses],
            "problematic_count": len(problematic_terminals),
            "problematic_terminals": [
                {
                    "terminal_id": t.terminal_id,
                    "name": t.name,
                    "location": t.location,
                    "last_heartbeat": t.last_heartbeat.isoformat() if t.last_heartbeat else None
                }
                for t in problematic_terminals
            ]
        },
        "recent_errors": [
            {
                "transaction_id": t.transaction_id,
                "terminal_id": t.terminal_id,
                "amount": t.amount,
                "error": t.bank_response,
                "timestamp": t.created_at.isoformat()
            }
            for t in recent_errors
        ],
        "system_health": {
            "overall_status": "healthy" if database_status == "healthy" and len(problematic_terminals) == 0 else "warning",
            "uptime": "N/A",  # В реальной системе получать время работы
            "version": "1.0.0"
        }
    }

@router.post("/maintenance-mode")
async def toggle_maintenance_mode(
    enabled: bool,
    current_user: User = Depends(get_current_admin_user),
    db: Session = Depends(get_db)
):
    """Включение/выключение режима обслуживания для всех терминалов"""
    
    if enabled:
        # Переводим все онлайн терминалы в режим обслуживания
        updated = db.query(Terminal).filter(Terminal.status == TerminalStatus.ONLINE).update(
            {"status": TerminalStatus.MAINTENANCE}
        )
        message = f"Режим обслуживания включен для {updated} терминалов"
    else:
        # Переводим все терминалы из режима обслуживания в онлайн
        updated = db.query(Terminal).filter(Terminal.status == TerminalStatus.MAINTENANCE).update(
            {"status": TerminalStatus.ONLINE}
        )
        message = f"Режим обслуживания отключен для {updated} терминалов"
    
    db.commit()
    
    return {"message": message, "affected_terminals": updated}

@router.get("/logs")
async def get_system_logs(
    skip: int = Query(0, ge=0),
    limit: int = Query(100, ge=1, le=1000),
    level: Optional[str] = Query(None, regex="^(ERROR|WARN|INFO|DEBUG)$"),
    current_user: User = Depends(get_current_admin_user),
    db: Session = Depends(get_db)
):
    """Получение системных логов (в реальной системе из файлов или ELK)"""
    
    # В реальной системе здесь была бы интеграция с системой логирования
    # Пока возвращаем заглушку
    
    logs = [
        {
            "timestamp": datetime.utcnow().isoformat(),
            "level": "INFO",
            "service": "api",
            "message": "System running normally",
            "details": {}
        }
    ]
    
    return {
        "logs": logs,
        "total": len(logs),
        "filters": {
            "level": level,
            "skip": skip,
            "limit": limit
        }
    } 