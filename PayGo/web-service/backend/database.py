from sqlalchemy import create_engine, MetaData
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import sessionmaker
from databases import Database
import asyncio

from config import settings

# Создание движка базы данных
engine = create_engine(settings.DATABASE_URL)
metadata = MetaData()

# Базовый класс для моделей
Base = declarative_base()

# Асинхронная база данных для FastAPI
database = Database(settings.DATABASE_URL)

# Сессия для синхронных операций
SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)

# Dependency для получения сессии БД
async def get_database():
    return database

def get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()

# Инициализация базы данных
async def init_db():
    """Инициализация соединения с базой данных"""
    await database.connect()
    print("✅ Подключение к базе данных установлено")

async def close_db():
    """Закрытие соединения с базой данных"""
    await database.disconnect()
    print("❌ Соединение с базой данных закрыто")

# Создание всех таблиц
def create_tables():
    """Создание всех таблиц в базе данных"""
    from models import user, terminal, transaction, card  # Импорт моделей
    Base.metadata.create_all(bind=engine)
    print("✅ Таблицы созданы успешно") 