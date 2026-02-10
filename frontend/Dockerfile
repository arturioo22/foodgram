# Stage 1: Build
FROM node:18-alpine AS build

WORKDIR /app

# Копируем package.json первыми для лучшего кэширования
COPY package.json package-lock.json ./
RUN npm install --silent

# Копируем остальные файлы
COPY . .

# Сборка приложения
ARG REACT_APP_API_URL
ENV REACT_APP_API_URL=${REACT_APP_API_URL:-/api}
RUN npm run build

# Stage 2: Serve
FROM nginx:alpine

# Копируем собранное приложение в nginx
COPY --from=build /app/build /usr/share/nginx/html

# Копируем конфигурацию nginx для SPA
COPY nginx-spa.conf /etc/nginx/conf.d/default.conf

EXPOSE 80

CMD ["nginx", "-g", "daemon off;"]