from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from fastapi.middleware.trustedhost import TrustedHostMiddleware
from fastapi.security import HTTPBearer
import uvicorn
from contextlib import asynccontextmanager

from routers import auth, users, terminals, transactions, cards, admin
from database import init_db
from config import settings

# Инициализация базы данных при старте
@asynccontextmanager
async def lifespan(app: FastAPI):
    # Startup
    await init_db()
    yield
    # Shutdown
    pass

# Создание FastAPI приложения
app = FastAPI(
    title="PayGo API",
    description="API для системы платежных терминалов PayGo",
    version="1.0.0",
    docs_url="/api/docs",
    redoc_url="/api/redoc",
    openapi_url="/api/openapi.json",
    lifespan=lifespan
)

# Security
security = HTTPBearer()

# Middleware
app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.ALLOWED_HOSTS,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

app.add_middleware(
    TrustedHostMiddleware,
    allowed_hosts=settings.ALLOWED_HOSTS
)

# Подключение роутеров
app.include_router(auth.router, prefix="/api/v1/auth", tags=["Аутентификация"])
app.include_router(users.router, prefix="/api/v1/users", tags=["Пользователи"])
app.include_router(terminals.router, prefix="/api/v1/terminals", tags=["Терминалы"])
app.include_router(transactions.router, prefix="/api/v1/transactions", tags=["Транзакции"])
app.include_router(cards.router, prefix="/api/v1/cards", tags=["Карты"])
app.include_router(admin.router, prefix="/api/v1/admin", tags=["Администрирование"])

# Основные эндпоинты
@app.get("/")
async def root():
    return {
        "message": "PayGo API Server",
        "version": "1.0.0",
        "status": "running"
    }

@app.get("/api/health")
async def health_check():
    return {
        "status": "healthy",
        "service": "paygo-api",
        "version": "1.0.0"
    }

# Запуск сервера
if __name__ == "__main__":
    uvicorn.run(
        "main:app",
        host=settings.API_HOST,
        port=settings.API_PORT,
        reload=settings.DEBUG,
        log_level="info"
    ) 