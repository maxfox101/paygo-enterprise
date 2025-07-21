from fastapi import APIRouter, HTTPException, Depends, status, Query
from sqlalchemy.orm import Session
from typing import List, Optional
from datetime import datetime, timedelta
from sqlalchemy import func

from models.terminal import (
    Terminal, TerminalCreate, TerminalUpdate, TerminalResponse,
    TerminalHeartbeat, TerminalConfig, TerminalStats, TerminalStatus
)
from database import get_db
from auth_utils import get_current_user, get_current_admin_user
from models.user import User

router = APIRouter()

@router.get("/", response_model=List[TerminalResponse])
async def get_terminals(
    skip: int = Query(0, ge=0),
    limit: int = Query(100, ge=1, le=1000),
    status: Optional[TerminalStatus] = None,
    current_user: User = Depends(get_current_admin_user),
    db: Session = Depends(get_db)
):
    """Получение списка терминалов (только для администраторов)"""
    
    query = db.query(Terminal)
    
    if status:
        query = query.filter(Terminal.status == status)
    
    terminals = query.offset(skip).limit(limit).all()
    return terminals

@router.post("/", response_model=TerminalResponse, status_code=status.HTTP_201_CREATED)
async def create_terminal(
    terminal_data: TerminalCreate,
    current_user: User = Depends(get_current_admin_user),
    db: Session = Depends(get_db)
):
    """Создание нового терминала"""
    
    # Проверка уникальности terminal_id
    existing_terminal = db.query(Terminal).filter(Terminal.terminal_id == terminal_data.terminal_id).first()
    if existing_terminal:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Терминал с таким ID уже существует"
        )
    
    # Создание терминала
    db_terminal = Terminal(
        terminal_id=terminal_data.terminal_id,
        name=terminal_data.name,
        location=terminal_data.location,
        address=terminal_data.address,
        terminal_type=terminal_data.terminal_type,
        status=TerminalStatus.OFFLINE
    )
    
    db.add(db_terminal)
    db.commit()
    db.refresh(db_terminal)
    
    return db_terminal

@router.get("/{terminal_id}", response_model=TerminalResponse)
async def get_terminal(
    terminal_id: str,
    current_user: User = Depends(get_current_admin_user),
    db: Session = Depends(get_db)
):
    """Получение информации о терминале"""
    
    terminal = db.query(Terminal).filter(Terminal.terminal_id == terminal_id).first()
    if not terminal:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Терминал не найден"
        )
    
    return terminal

@router.put("/{terminal_id}", response_model=TerminalResponse)
async def update_terminal(
    terminal_id: str,
    terminal_update: TerminalUpdate,
    current_user: User = Depends(get_current_admin_user),
    db: Session = Depends(get_db)
):
    """Обновление информации о терминале"""
    
    terminal = db.query(Terminal).filter(Terminal.terminal_id == terminal_id).first()
    if not terminal:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Терминал не найден"
        )
    
    # Обновление полей
    update_data = terminal_update.dict(exclude_unset=True)
    for field, value in update_data.items():
        setattr(terminal, field, value)
    
    terminal.updated_at = datetime.utcnow()
    db.commit()
    db.refresh(terminal)
    
    return terminal

@router.delete("/{terminal_id}")
async def delete_terminal(
    terminal_id: str,
    current_user: User = Depends(get_current_admin_user),
    db: Session = Depends(get_db)
):
    """Удаление терминала"""
    
    terminal = db.query(Terminal).filter(Terminal.terminal_id == terminal_id).first()
    if not terminal:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Терминал не найден"
        )
    
    db.delete(terminal)
    db.commit()
    
    return {"message": "Терминал успешно удален"}

@router.post("/heartbeat")
async def terminal_heartbeat(
    heartbeat_data: TerminalHeartbeat,
    db: Session = Depends(get_db)
):
    """Получение heartbeat от терминала"""
    
    terminal = db.query(Terminal).filter(Terminal.terminal_id == heartbeat_data.terminal_id).first()
    if not terminal:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Терминал не найден"
        )
    
    # Обновление статуса и времени последнего heartbeat
    terminal.status = heartbeat_data.status
    terminal.last_heartbeat = datetime.utcnow()
    
    if heartbeat_data.ip_address:
        terminal.ip_address = heartbeat_data.ip_address
    
    if heartbeat_data.hardware_info:
        terminal.hardware_info = heartbeat_data.hardware_info
    
    if heartbeat_data.current_transaction_count is not None:
        terminal.total_transactions = heartbeat_data.current_transaction_count
    
    db.commit()
    
    return {"message": "Heartbeat получен", "terminal_status": "updated"}

@router.get("/{terminal_id}/config", response_model=TerminalConfig)
async def get_terminal_config(
    terminal_id: str,
    db: Session = Depends(get_db)
):
    """Получение конфигурации терминала"""
    
    terminal = db.query(Terminal).filter(Terminal.terminal_id == terminal_id).first()
    if not terminal:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Терминал не найден"
        )
    
    # Если конфигурации нет, возвращаем дефолтную
    if not terminal.config:
        return TerminalConfig()
    
    return TerminalConfig(**terminal.config)

@router.put("/{terminal_id}/config")
async def update_terminal_config(
    terminal_id: str,
    config: TerminalConfig,
    current_user: User = Depends(get_current_admin_user),
    db: Session = Depends(get_db)
):
    """Обновление конфигурации терминала"""
    
    terminal = db.query(Terminal).filter(Terminal.terminal_id == terminal_id).first()
    if not terminal:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Терминал не найден"
        )
    
    terminal.config = config.dict()
    terminal.updated_at = datetime.utcnow()
    db.commit()
    
    return {"message": "Конфигурация обновлена"}

@router.get("/{terminal_id}/stats", response_model=TerminalStats)
async def get_terminal_stats(
    terminal_id: str,
    days: int = Query(30, ge=1, le=365),
    current_user: User = Depends(get_current_admin_user),
    db: Session = Depends(get_db)
):
    """Получение статистики терминала"""
    
    terminal = db.query(Terminal).filter(Terminal.terminal_id == terminal_id).first()
    if not terminal:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Терминал не найден"
        )
    
    # Период статистики
    period_end = datetime.utcnow()
    period_start = period_end - timedelta(days=days)
    
    # Здесь должна быть логика подсчета статистики из транзакций
    # Пока возвращаем заглушку
    
    stats = TerminalStats(
        terminal_id=terminal_id,
        period_start=period_start,
        period_end=period_end,
        transactions_count=terminal.total_transactions,
        successful_transactions=terminal.total_transactions,  # Заглушка
        failed_transactions=0,  # Заглушка
        total_amount=terminal.total_amount,
        average_amount=terminal.total_amount / max(terminal.total_transactions, 1),
        uptime_percentage=95.5,  # Заглушка
        error_count=0  # Заглушка
    )
    
    return stats

@router.post("/{terminal_id}/maintenance")
async def set_terminal_maintenance(
    terminal_id: str,
    enable: bool = True,
    current_user: User = Depends(get_current_admin_user),
    db: Session = Depends(get_db)
):
    """Включение/выключение режима обслуживания терминала"""
    
    terminal = db.query(Terminal).filter(Terminal.terminal_id == terminal_id).first()
    if not terminal:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Терминал не найден"
        )
    
    if enable:
        terminal.status = TerminalStatus.MAINTENANCE
        message = "Режим обслуживания включен"
    else:
        terminal.status = TerminalStatus.ONLINE
        message = "Режим обслуживания выключен"
    
    terminal.updated_at = datetime.utcnow()
    db.commit()
    
    return {"message": message}

@router.get("/status/summary")
async def get_terminals_summary(
    current_user: User = Depends(get_current_admin_user),
    db: Session = Depends(get_db)
):
    """Получение сводной статистики по всем терминалам"""
    
    # Подсчет терминалов по статусам
    total_terminals = db.query(Terminal).count()
    online_terminals = db.query(Terminal).filter(Terminal.status == TerminalStatus.ONLINE).count()
    offline_terminals = db.query(Terminal).filter(Terminal.status == TerminalStatus.OFFLINE).count()
    maintenance_terminals = db.query(Terminal).filter(Terminal.status == TerminalStatus.MAINTENANCE).count()
    error_terminals = db.query(Terminal).filter(Terminal.status == TerminalStatus.ERROR).count()
    
    # Общая статистика
    total_transactions = db.query(func.sum(Terminal.total_transactions)).scalar() or 0
    total_amount = db.query(func.sum(Terminal.total_amount)).scalar() or 0.0
    
    return {
        "total_terminals": total_terminals,
        "online_terminals": online_terminals,
        "offline_terminals": offline_terminals,
        "maintenance_terminals": maintenance_terminals,
        "error_terminals": error_terminals,
        "total_transactions": total_transactions,
        "total_amount": total_amount,
        "average_amount": total_amount / max(total_transactions, 1)
    } 