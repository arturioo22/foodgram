FROM python:3.11-slim

# Устанавливаем рабочую директорию
WORKDIR /app

# Устанавливаем системные зависимости
RUN apt-get update && apt-get install -y \
    gcc \
    libpq-dev \
    postgresql-client \
    curl \
    && rm -rf /var/lib/apt/lists/*

# Копируем зависимости
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# Копируем весь проект
COPY . .

# Создаем папки для статики и медиа
RUN mkdir -p static media

# Компилируем статику
RUN python manage.py collectstatic --noinput

# Открываем порт
EXPOSE 8000

# Запускаем приложение
CMD ["gunicorn", "--bind", "0.0.0.0:8000", "--workers", "3", "foodgram.wsgi:application"]