# Многоступенчатая сборка
FROM node:18-alpine AS builder

WORKDIR /app

# Копирование package.json и установка зависимостей
COPY package*.json ./
RUN npm ci --only=production

# Копирование исходного кода и сборка
COPY . .
RUN npm run build

# Продакшн образ с Nginx
FROM nginx:alpine

# Копирование собранного приложения
COPY --from=builder /app/build /usr/share/nginx/html

# Копирование конфигурации Nginx
COPY nginx.conf /etc/nginx/conf.d/default.conf

# Открытие порта
EXPOSE 80

CMD ["nginx", "-g", "daemon off;"] 