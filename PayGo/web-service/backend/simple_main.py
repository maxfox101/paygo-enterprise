#!/usr/bin/env python3
"""
Упрощенный запуск PayGo API сервера для демонстрации
Без подключения к базе данных - только основные эндпоинты
"""

from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel
import uvicorn
from datetime import datetime
from typing import List, Optional

# Создание приложения
app = FastAPI(
    title="PayGo API Demo",
    description="Демо версия API для системы платежных терминалов PayGo",
    version="1.0.0",
    docs_url="/api/docs",
    redoc_url="/api/redoc"
)

# CORS middleware
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Модели данных
class HealthResponse(BaseModel):
    status: str
    service: str
    version: str
    timestamp: datetime

class TerminalInfo(BaseModel):
    terminal_id: str
    name: str
    location: str
    status: str
    last_heartbeat: Optional[datetime] = None

class TransactionInfo(BaseModel):
    transaction_id: str
    amount: float
    status: str
    payment_method: str
    created_at: datetime

class DashboardStats(BaseModel):
    total_terminals: int
    online_terminals: int
    total_transactions: int
    total_amount: float

# Демо данные
demo_terminals = [
    TerminalInfo(
        terminal_id="DEMO_001", 
        name="Демо терминал 1", 
        location="Офис PayGo", 
        status="online",
        last_heartbeat=datetime.now()
    ),
    TerminalInfo(
        terminal_id="DEMO_002", 
        name="Демо терминал 2", 
        location="ТЦ Горизонт", 
        status="online",
        last_heartbeat=datetime.now()
    ),
    TerminalInfo(
        terminal_id="DEMO_003", 
        name="Демо терминал 3", 
        location="Аэропорт", 
        status="offline"
    )
]

demo_transactions = [
    TransactionInfo(
        transaction_id="TXN_001", 
        amount=1500.0, 
        status="completed", 
        payment_method="nfc_card",
        created_at=datetime.now()
    ),
    TransactionInfo(
        transaction_id="TXN_002", 
        amount=250.0, 
        status="completed", 
        payment_method="qr_code",
        created_at=datetime.now()
    ),
    TransactionInfo(
        transaction_id="TXN_003", 
        amount=3200.0, 
        status="pending", 
        payment_method="biometry_face",
        created_at=datetime.now()
    )
]

# Эндпоинты

@app.get("/")
async def root():
    return {
        "message": "🚀 PayGo API сервер запущен успешно!",
        "version": "1.0.0",
        "status": "running",
        "docs": "/api/docs",
        "timestamp": datetime.now()
    }

@app.get("/api/health", response_model=HealthResponse)
async def health_check():
    return HealthResponse(
        status="healthy",
        service="paygo-api-demo",
        version="1.0.0",
        timestamp=datetime.now()
    )

@app.get("/api/v1/terminals", response_model=List[TerminalInfo])
async def get_terminals():
    """Получение списка демо терминалов"""
    return demo_terminals

@app.get("/api/v1/terminals/{terminal_id}", response_model=TerminalInfo)
async def get_terminal(terminal_id: str):
    """Получение информации о конкретном терминале"""
    for terminal in demo_terminals:
        if terminal.terminal_id == terminal_id:
            return terminal
    raise HTTPException(status_code=404, detail="Терминал не найден")

@app.get("/api/v1/transactions", response_model=List[TransactionInfo])
async def get_transactions():
    """Получение списка демо транзакций"""
    return demo_transactions

@app.get("/api/v1/transactions/{transaction_id}", response_model=TransactionInfo)
async def get_transaction(transaction_id: str):
    """Получение информации о конкретной транзакции"""
    for transaction in demo_transactions:
        if transaction.transaction_id == transaction_id:
            return transaction
    raise HTTPException(status_code=404, detail="Транзакция не найдена")

@app.get("/api/v1/admin/dashboard", response_model=DashboardStats)
async def get_dashboard():
    """Получение статистики для админ панели"""
    online_count = sum(1 for t in demo_terminals if t.status == "online")
    total_amount = sum(t.amount for t in demo_transactions if t.status == "completed")
    
    return DashboardStats(
        total_terminals=len(demo_terminals),
        online_terminals=online_count,
        total_transactions=len(demo_transactions),
        total_amount=total_amount
    )

@app.post("/api/v1/terminals/heartbeat")
async def terminal_heartbeat(terminal_id: str, status: str):
    """Получение heartbeat от терминала"""
    for terminal in demo_terminals:
        if terminal.terminal_id == terminal_id:
            terminal.status = status
            terminal.last_heartbeat = datetime.now()
            return {"message": "Heartbeat получен", "terminal_id": terminal_id}
    
    return {"message": "Новый терминал зарегистрирован", "terminal_id": terminal_id}

@app.post("/api/v1/transactions/payment-request")
async def create_payment(terminal_id: str, amount: float, payment_method: str):
    """Создание запроса на платеж"""
    transaction_id = f"TXN_{len(demo_transactions) + 1:03d}"
    
    new_transaction = TransactionInfo(
        transaction_id=transaction_id,
        amount=amount,
        status="pending",
        payment_method=payment_method,
        created_at=datetime.now()
    )
    
    demo_transactions.append(new_transaction)
    
    return {
        "transaction_id": transaction_id,
        "status": "pending",
        "amount": amount,
        "expires_at": datetime.now()
    }

@app.get("/api/v1/stats/system")
async def get_system_stats():
    """Системная статистика"""
    return {
        "system_status": "healthy",
        "uptime": "Demo Mode",
        "version": "1.0.0",
        "terminals": {
            "total": len(demo_terminals),
            "online": sum(1 for t in demo_terminals if t.status == "online"),
            "offline": sum(1 for t in demo_terminals if t.status == "offline")
        },
        "transactions": {
            "total": len(demo_transactions),
            "completed": sum(1 for t in demo_transactions if t.status == "completed"),
            "pending": sum(1 for t in demo_transactions if t.status == "pending")
        },
        "financial": {
            "total_amount": sum(t.amount for t in demo_transactions if t.status == "completed"),
            "average_transaction": sum(t.amount for t in demo_transactions if t.status == "completed") / max(sum(1 for t in demo_transactions if t.status == "completed"), 1)
        }
    }

# Запуск сервера
if __name__ == "__main__":
    print("🚀 Запуск PayGo API Demo сервера...")
    print("📍 Адрес: http://localhost:8000")
    print("📚 Документация: http://localhost:8000/api/docs")
    print("💓 Здоровье системы: http://localhost:8000/api/health")
    print("-" * 60)
    
    uvicorn.run(
        "simple_main:app",
        host="0.0.0.0",
        port=8000,
        reload=True,
        log_level="info"
    ) 