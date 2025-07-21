#!/usr/bin/env python3
"""
Скрипт запуска PayGo API сервера
"""

import uvicorn
from config import settings

if __name__ == "__main__":
    print(f"🚀 Запуск PayGo API сервера v{settings.VERSION}")
    print(f"📍 Адрес: {settings.API_HOST}:{settings.API_PORT}")
    print(f"🔧 Режим отладки: {settings.DEBUG}")
    print(f"📊 Документация: http://{settings.API_HOST}:{settings.API_PORT}/api/docs")
    print("-" * 60)
    
    uvicorn.run(
        "main:app",
        host=settings.API_HOST,
        port=settings.API_PORT,
        reload=settings.DEBUG,
        log_level="info",
        access_log=True
    ) 