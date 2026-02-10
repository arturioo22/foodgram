FROM nginx:1.22.1-alpine

# Удаляем дефолтный конфиг
RUN rm /etc/nginx/conf.d/default.conf

# Копируем наш конфиг
COPY nginx.conf /etc/nginx/conf.d/

# Создаем директории для статики
RUN mkdir -p /static /media

EXPOSE 80

CMD ["nginx", "-g", "daemon off;"]