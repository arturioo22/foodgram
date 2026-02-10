# Stage 1: Build
FROM node:18-alpine as build

WORKDIR /app

# Кэширование зависимостей
COPY package*.json ./
RUN npm ci --silent

# Копирование исходного кода
COPY . .

# Сборка приложения
ARG REACT_APP_API_URL
ENV REACT_APP_API_URL=${REACT_APP_API_URL:-/api}
RUN npm run build

# Stage 2: Serve
FROM nginx:alpine

# Копирование собранного приложения
COPY --from=build /app/build /usr/share/nginx/html

# Базовая конфигурация nginx для SPA
COPY nginx-spa.conf /etc/nginx/conf.d/default.conf

# Открываем порт 80
EXPOSE 80

CMD ["nginx", "-g", "daemon off;"]