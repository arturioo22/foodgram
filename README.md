Foodgram - Продуктовый помощник
Описание проекта
Foodgram — это онлайн-сервис, где пользователи могут публиковать рецепты, подписываться на публикации других авторов, добавлять рецепты в избранное и формировать список покупок для выбранных блюд. Проект реализован с полной контейнеризацией и автоматическим CI/CD.

Основные функции
Публикация и редактирование рецептов

Фильтрация рецептов по тегам (завтрак, обед, ужин и др.)

Поиск ингредиентов по мере ввода

Подписка на любимых авторов

Добавление рецептов в избранное

Формирование и скачивание списка покупок

Загрузка аватаров пользователей

Docker-контейнеризация

Автоматический CI/CD через GitHub Actions

Стек технологий
Backend
Django 4.2 - веб-фреймворк

Django REST Framework - построение REST API

PostgreSQL 15 - реляционная база данных

Djoser 2.3.3 - аутентификация и управление пользователями

Pillow - работа с изображениями

Gunicorn - WSGI HTTP-сервер

django-filter - фильтрация запросов

Frontend
React - пользовательский интерфейс

Nginx - веб-сервер для отдачи статики

Инфраструктура
Docker — контейнеризация

Docker Compose — оркестрация

Nginx — reverse-proxy и балансировка

GitHub Actions — CI/CD

Docker Hub — реестр образов

Развертывание проекта
Предварительные требования
Docker и Docker Compose

Python 3.10+ (для локальной разработки)

Node.js 18+ (для локальной разработки фронтенда)

Git

1. Клонирование репозитория
git clone https://github.com/arturioo22/foodgram.git
cd foodgram
2. Настройка переменных окружения
Создайте файл .env в корневой директории для разработки:

# Django
SECRET_KEY=your-secret-key-here
DEBUG=True
ALLOWED_HOSTS=localhost,127.0.0.1,backend,frontend
CSRF_TRUSTED_ORIGINS=http://localhost,http://127.0.0.1
CORS_ALLOWED_ORIGINS=http://localhost,http://127.0.0.1

# Database
DB_NAME=foodgram_dev
DB_USER=foodgram_user
DB_PASSWORD=dev_password
DB_HOST=db
DB_PORT=5432

# Superuser (optional)
DJANGO_SUPERUSER_USERNAME=admin
DJANGO_SUPERUSER_EMAIL=admin@example.com
DJANGO_SUPERUSER_PASSWORD=admin123
Для продакшена создайте файл .env.production:

# Django
SECRET_KEY=your-production-secret-key
DEBUG=False
ALLOWED_HOSTS=fffoooddgramm.ddns.net,localhost,127.0.0.1,backend,frontend,gateway
CSRF_TRUSTED_ORIGINS=https://fffoooddgramm.ddns.net,http://fffoooddgramm.ddns.net
CORS_ALLOWED_ORIGINS=https://fffoooddgramm.ddns.net,http://fffoooddgramm.ddns.net

# Database
DB_NAME=foodgram
DB_USER=foodgram_user
DB_PASSWORD=your-db-password
DB_HOST=db
DB_PORT=5432
3. Запуск в режиме разработки
# Сборка и запуск контейнеров
docker-compose up -d --build

# Применение миграций
docker-compose exec backend python manage.py migrate

# Загрузка фикстур с ингредиентами
docker-compose exec backend python manage.py loaddata /app/data/ingredients.json

# Сбор статики
docker-compose exec backend python manage.py collectstatic --noinput
Сайт будет доступен по адресу: http://localhost:8000
API: http://localhost:8000/api/
Админ-панель: http://localhost:8000/admin/

4. Запуск в production
# Запуск контейнеров
docker-compose -f docker-compose.production.yml up -d

# Применение миграций
docker-compose -f docker-compose.production.yml exec backend python manage.py migrate --noinput

# Первоначальная настройка базы данных (ингредиенты, теги, суперпользователь)
./scripts/init_db.sh

# Сбор статики
docker-compose -f docker-compose.production.yml exec backend python manage.py collectstatic --noinput
CI/CD и автоматический деплой
Проект использует GitHub Actions для автоматического тестирования, сборки образов и деплоя на сервер.

Процесс деплоя
Пуш в ветку main запускает workflow

Запускаются тесты (flake8, Django tests)

Собираются Docker-образы:

arturioo22/foodgram_backend:latest

arturioo22/foodgram_frontend:latest

arturioo22/foodgram_gateway:latest

Образы публикуются на Docker Hub

По SSH подключается к серверу и выполняет деплой

Автоматически применяются миграции и загружаются фикстуры с ингредиентами (если база пуста)

Настройка секретов GitHub Actions
Для работы CI/CD необходимо добавить следующие секреты в репозитории:

Секрет	Описание
DOCKERHUB_USERNAME	Имя пользователя Docker Hub
DOCKERHUB_TOKEN	Токен доступа к Docker Hub
HOST	IP-адрес сервера
USER	Имя пользователя на сервере
SSH_KEY	Приватный SSH-ключ
PASSPHRASE	Пароль от SSH-ключа (если есть)
SECRET_KEY	Секретный ключ Django
DB_PASSWORD	Пароль базы данных

## API

API доступно по адресу: `https://fffoooddgramm.ddns.net/api/`

Основные эндпоинты:
- `api/users/` — пользователи
- `api/recipes/` — рецепты
- `api/ingredients/` — ингредиенты
- `api/tags/` — теги

При переходе по ссылкам в браузере открывается интерактивный интерфейс Django REST Framework.

Основные эндпоинты
Метод	URL	Описание
POST	/api/auth/token/login/	Получение токена
POST	/api/users/	Регистрация
GET	/api/users/me/	Текущий пользователь
POST	/api/users/set_password/	Изменение пароля
GET	/api/users/{id}/	Профиль пользователя
GET	/api/recipes/	Список рецептов
POST	/api/recipes/	Создание рецепта
GET	/api/recipes/{id}/	Детали рецепта
PATCH	/api/recipes/{id}/	Редактирование рецепта
DELETE	/api/recipes/{id}/	Удаление рецепта
POST	/api/recipes/{id}/favorite/	Добавить в избранное
DELETE	/api/recipes/{id}/favorite/	Удалить из избранного
POST	/api/recipes/{id}/shopping_cart/	Добавить в корзину
DELETE	/api/recipes/{id}/shopping_cart/	Удалить из корзины
GET	/api/recipes/download_shopping_cart/	Скачать список покупок
GET	/api/tags/	Список тегов
GET	/api/ingredients/	Список ингредиентов
GET	/api/ingredients/?name={query}	Поиск ингредиентов
Особенности реализации
База ингредиентов
Проект включает 2186 предустановленных ингредиентов с единицами измерения

Фикстуры автоматически загружаются при первом деплое

Поддержка поиска по началу названия (istartswith)

Аутентификация
JWT-подобная аутентификация через токены (Djoser)

Email используется в качестве основного идентификатора

Возможность изменения пароля и загрузки аватара

Права доступа
Только автор может редактировать/удалять рецепт

Подписываться можно на любого пользователя

Нельзя подписаться на самого себя

Тестирование
# Запуск тестов backend
cd backend
python manage.py test

# Запуск линтера
python -m flake8 .
Автор
Фисунов Артур

Email: fisunov.arthur@yandex.ru

GitHub: arturioo22

Ссылки для проверки
Ресурс	URL
Репозиторий	https://github.com/arturioo22/foodgram
Workflow	[![Main Workflow](https://github.com/arturioo22/foodgram/actions/workflows/main.yml/badge.svg)](https://github.com/arturioo22/foodgram/actions/workflows/main.yml)
Production	http://fffoooddgramm.ddns.net
API	http://fffoooddgramm.ddns.net/api/
Админ-панель	http://fffoooddgramm.ddns.net/admin/
Docker Hub	https://hub.docker.com/u/arturioo22
