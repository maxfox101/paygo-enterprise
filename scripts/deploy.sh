#!/bin/bash

# PayGo Deployment Script
# Скрипт для развертывания системы PayGo

set -e

echo "🚀 Начинаем развертывание PayGo..."

# Цвета для вывода
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m' # No Color

# Функция для логирования
log() {
    echo -e "${GREEN}[$(date +'%Y-%m-%d %H:%M:%S')] $1${NC}"
}

warn() {
    echo -e "${YELLOW}[$(date +'%Y-%m-%d %H:%M:%S')] WARNING: $1${NC}"
}

error() {
    echo -e "${RED}[$(date +'%Y-%m-%d %H:%M:%S')] ERROR: $1${NC}"
    exit 1
}

# Проверка зависимостей
check_dependencies() {
    log "Проверка зависимостей..."
    
    if ! command -v docker &> /dev/null; then
        error "Docker не установлен"
    fi
    
    if ! command -v docker-compose &> /dev/null; then
        error "Docker Compose не установлен"
    fi
    
    log "✅ Все зависимости установлены"
}

# Создание необходимых директорий
create_directories() {
    log "Создание директорий..."
    
    mkdir -p backups
    mkdir -p config/ssl
    mkdir -p config/grafana/dashboards
    mkdir -p config/grafana/datasources
    mkdir -p logs
    mkdir -p web-service/backend/uploads
    
    log "✅ Директории созданы"
}

# Генерация SSL сертификатов для разработки
generate_ssl_certs() {
    if [ ! -f "config/ssl/cert.pem" ]; then
        log "Генерация SSL сертификатов для разработки..."
        
        openssl req -x509 -nodes -days 365 -newkey rsa:2048 \
            -keyout config/ssl/key.pem \
            -out config/ssl/cert.pem \
            -subj "/C=RU/ST=Rostov/L=Rostov-on-Don/O=PayGo/CN=localhost"
        
        log "✅ SSL сертификаты созданы"
    else
        log "SSL сертификаты уже существуют"
    fi
}

# Создание конфигурации Grafana
create_grafana_config() {
    log "Создание конфигурации Grafana..."
    
    # Datasource для Prometheus
    cat > config/grafana/datasources/prometheus.yml << EOF
apiVersion: 1
datasources:
  - name: Prometheus
    type: prometheus
    access: proxy
    url: http://prometheus:9090
    isDefault: true
EOF

    # Основной dashboard
    cat > config/grafana/dashboards/paygo-dashboard.json << 'EOF'
{
  "dashboard": {
    "id": null,
    "title": "PayGo System Dashboard",
    "tags": ["paygo"],
    "timezone": "Europe/Moscow",
    "panels": [
      {
        "id": 1,
        "title": "System Health",
        "type": "stat",
        "targets": [
          {
            "expr": "up{job=\"paygo-backend\"}",
            "legendFormat": "Backend Status"
          }
        ],
        "gridPos": {"h": 8, "w": 12, "x": 0, "y": 0}
      }
    ],
    "time": {
      "from": "now-1h",
      "to": "now"
    },
    "refresh": "30s"
  }
}
EOF

    log "✅ Конфигурация Grafana создана"
}

# Проверка переменных окружения
check_env_vars() {
    log "Проверка переменных окружения..."
    
    if [ -f ".env" ]; then
        log "Файл .env найден"
        source .env
    else
        warn "Файл .env не найден, создаем с базовыми настройками..."
        cat > .env << EOF
# PayGo Environment Variables
DATABASE_URL=postgresql://paygo_user:paygo_password@database:5432/paygo_db
REDIS_URL=redis://:paygo_redis_password@redis:6379
SECRET_KEY=$(openssl rand -hex 32)
DEBUG=False
ALLOWED_HOSTS=localhost,127.0.0.1,0.0.0.0
EOF
    fi
    
    log "✅ Переменные окружения настроены"
}

# Сборка и запуск контейнеров
deploy_containers() {
    log "Сборка и запуск контейнеров..."
    
    # Остановка существующих контейнеров
    docker-compose down --remove-orphans
    
    # Сборка образов
    docker-compose build --no-cache
    
    # Запуск в фоновом режиме
    docker-compose up -d
    
    log "✅ Контейнеры запущены"
}

# Ожидание готовности сервисов
wait_for_services() {
    log "Ожидание готовности сервисов..."
    
    # Ждем PostgreSQL
    echo -n "Ожидание PostgreSQL... "
    while ! docker-compose exec -T database pg_isready -U paygo_user -d paygo_db >/dev/null 2>&1; do
        echo -n "."
        sleep 2
    done
    echo " ✅"
    
    # Ждем Redis
    echo -n "Ожидание Redis... "
    while ! docker-compose exec -T redis redis-cli ping >/dev/null 2>&1; do
        echo -n "."
        sleep 2
    done
    echo " ✅"
    
    # Ждем Backend
    echo -n "Ожидание Backend... "
    while ! curl -f http://localhost:8000/api/health >/dev/null 2>&1; do
        echo -n "."
        sleep 2
    done
    echo " ✅"
    
    # Ждем Frontend
    echo -n "Ожидание Frontend... "
    while ! curl -f http://localhost:3000 >/dev/null 2>&1; do
        echo -n "."
        sleep 2
    done
    echo " ✅"
    
    log "✅ Все сервисы готовы"
}

# Инициализация базы данных
init_database() {
    log "Инициализация базы данных..."
    
    # Выполнение миграций
    docker-compose exec backend alembic upgrade head
    
    log "✅ База данных инициализирована"
}

# Проверка работоспособности
health_check() {
    log "Проверка работоспособности системы..."
    
    # Проверка API
    if curl -f http://localhost:8000/api/health >/dev/null 2>&1; then
        log "✅ Backend API работает"
    else
        error "Backend API не отвечает"
    fi
    
    # Проверка Frontend
    if curl -f http://localhost:3000 >/dev/null 2>&1; then
        log "✅ Frontend работает"
    else
        error "Frontend не отвечает"
    fi
    
    # Проверка базы данных
    if docker-compose exec -T database pg_isready -U paygo_user -d paygo_db >/dev/null 2>&1; then
        log "✅ База данных доступна"
    else
        error "База данных недоступна"
    fi
    
    log "✅ Система работает корректно"
}

# Вывод информации о развертывании
show_info() {
    log "🎉 Развертывание завершено успешно!"
    echo ""
    echo -e "${BLUE}📋 Доступные сервисы:${NC}"
    echo "🌐 Frontend:     http://localhost:3000"
    echo "🔧 Backend API:  http://localhost:8000"
    echo "📊 Grafana:      http://localhost:3001 (admin/paygo_admin_password)"
    echo "📈 Prometheus:   http://localhost:9090"
    echo "🌸 Flower:       http://localhost:5555"
    echo "🗄️ PostgreSQL:   localhost:5432"
    echo "🔴 Redis:        localhost:6379"
    echo ""
    echo -e "${BLUE}📖 API Документация: http://localhost:8000/api/docs${NC}"
    echo ""
    echo -e "${YELLOW}💡 Полезные команды:${NC}"
    echo "  docker-compose logs -f                 # Просмотр логов"
    echo "  docker-compose exec backend bash       # Подключение к backend"
    echo "  docker-compose exec database psql -U paygo_user -d paygo_db  # PostgreSQL"
    echo "  docker-compose down                    # Остановка всех сервисов"
    echo ""
}

# Основная функция
main() {
    echo -e "${BLUE}"
    echo "╔═══════════════════════════════════════╗"
    echo "║          PayGo Deployment             ║"
    echo "║    Система Платежных Терминалов       ║"
    echo "╚═══════════════════════════════════════╝"
    echo -e "${NC}"
    
    check_dependencies
    create_directories
    generate_ssl_certs
    create_grafana_config
    check_env_vars
    deploy_containers
    wait_for_services
    init_database
    health_check
    show_info
}

# Обработка аргументов командной строки
case "${1:-deploy}" in
    "deploy")
        main
        ;;
    "stop")
        log "Остановка сервисов..."
        docker-compose down
        log "✅ Сервисы остановлены"
        ;;
    "restart")
        log "Перезапуск сервисов..."
        docker-compose restart
        log "✅ Сервисы перезапущены"
        ;;
    "logs")
        docker-compose logs -f
        ;;
    "health")
        health_check
        ;;
    *)
        echo "Использование: $0 {deploy|stop|restart|logs|health}"
        exit 1
        ;;
esac 