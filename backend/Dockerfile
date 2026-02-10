FROM python:3.10-slim

WORKDIR /app

# Установка зависимостей системы
RUN apt-get update && apt-get install -y \
    gcc \
    postgresql-client \
    && rm -rf /var/lib/apt/lists/*

# Копирование зависимостей Python
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# Копирование кода приложения
COPY . .

# Сборка статики и запуск сервера
CMD sh -c "python manage.py collectstatic --noinput && \
           python manage.py migrate --noinput && \
           gunicorn foodgram.wsgi:application --bind 0.0.0.0:8000"