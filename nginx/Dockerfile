FROM nginx:1.22.1

# Копируем конфиг
COPY nginx.conf /etc/nginx/templates/default.conf.template

# Создаем директории
RUN mkdir -p /static /media

# Устанавливаем права
RUN chown -R nginx:nginx /static /media