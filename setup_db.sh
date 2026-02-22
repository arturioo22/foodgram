#!/bin/bash

# Скрипт для полной перезагрузки базы данных.
# Очищает все данные и загружает заново. Без подтверждения!

set -e

exec_backend() {
    docker-compose -f docker-compose.production.yml exec -T backend "$@"
}

exec_db() {
    docker-compose -f docker-compose.production.yml exec -T db psql -U foodgram_user -d foodgram -t -c "$1"
}

echo "🔄 ПОЛНАЯ ПЕРЕЗАГРУЗКА БАЗЫ ДАННЫХ"
echo "====================================="

echo "1. Очистка существующих данных..."

# Отключаем проверку внешних ключей временно
exec_db "SET session_replication_role = 'replica';" 2>/dev/null || true

# Очищаем таблицы в правильном порядке (сначала зависимые)
echo "   - Удаление рецептов..."
exec_db "TRUNCATE TABLE recipes_recipe CASCADE;" 2>/dev/null || echo "      (таблица recipes_recipe не существует)"

echo "   - Удаление ингредиентов в рецептах..."
exec_db "TRUNCATE TABLE recipes_ingredientinrecipe CASCADE;" 2>/dev/null || echo "      (таблица ingredientinrecipe не существует)"

echo "   - Удаление избранного..."
exec_db "TRUNCATE TABLE recipes_favorite CASCADE;" 2>/dev/null || echo "      (таблица favorite не существует)"

echo "   - Удаление корзины..."
exec_db "TRUNCATE TABLE recipes_shoppingcart CASCADE;" 2>/dev/null || echo "      (таблица shoppingcart не существует)"

echo "   - Удаление тегов..."
exec_db "TRUNCATE TABLE recipes_tag CASCADE;" 2>/dev/null || echo "      (таблица tag не существует)"

echo "   - Удаление ингредиентов..."
exec_db "TRUNCATE TABLE recipes_ingredient CASCADE;" 2>/dev/null || echo "      (таблица ingredient не существует)"

echo "   - Удаление пользователей (кроме суперпользователей)..."
exec_db "DELETE FROM users_user WHERE is_superuser = false;" 2>/dev/null || echo "      (таблица users_user не существует)"

# Включаем обратно проверку внешних ключей
exec_db "SET session_replication_role = 'origin';" 2>/dev/null || true

echo "✅ Очистка завершена"
echo ""

echo "2. Применение миграций..."
exec_backend python manage.py migrate --noinput
echo "✅ Миграции применены"
echo ""

echo "3. Загрузка ингредиентов..."

# Копируем файл с ингредиентами
docker cp data/ingredients.json foodgram_backend_prod:/app/data/ingredients.json 2>/dev/null || {
    echo "   ⚠️  Файл ingredients.json не найден, пропускаем..."
}

# Конвертируем и загружаем
exec_backend python -c "
import json
import os

json_file = '/app/data/ingredients.json'
if os.path.exists(json_file):
    with open(json_file, 'r', encoding='utf-8') as f:
        ingredients = json.load(f)
    
    fixture = []
    for ing in ingredients:
        fixture.append({
            'model': 'recipes.ingredient',
            'fields': {
                'name': ing['name'],
                'measurement_unit': ing['measurement_unit']
            }
        })
    
    with open('/app/data/ingredients_fixture.json', 'w', encoding='utf-8') as f:
        json.dump(fixture, f, ensure_ascii=False, indent=2)
    
    from django.core.management import call_command
    call_command('loaddata', '/app/data/ingredients_fixture.json')
    print(f'✅ Загружено {len(fixture)} ингредиентов')
else:
    print('⚠️  Файл ingredients.json не найден, ингредиенты не загружены')
"

ING_COUNT=$(exec_db "SELECT COUNT(*) FROM recipes_ingredient;" | tr -d ' ')
echo "   Ингредиентов в базе: $ING_COUNT"
echo ""

echo "4. Создание тегов..."

exec_backend python manage.py shell << EOF
from recipes.models import Tag

tags = [
    {'name': 'Завтрак', 'color': '#E26C2D', 'slug': 'breakfast'},
    {'name': 'Обед', 'color': '#49B64E', 'slug': 'lunch'},
    {'name': 'Ужин', 'color': '#8775D2', 'slug': 'dinner'},
    {'name': 'Десерт', 'color': '#FFD700', 'slug': 'dessert'},
    {'name': 'Выпечка', 'color': '#FF6347', 'slug': 'baking'},
    {'name': 'Салат', 'color': '#32CD32', 'slug': 'salad'},
    {'name': 'Супы', 'color': '#1E90FF', 'slug': 'soup'},
    {'name': 'Напитки', 'color': '#9370DB', 'slug': 'drinks'},
]

for tag in tags:
    Tag.objects.get_or_create(**tag)

print(f'✅ Создано {Tag.objects.count()} тегов')
EOF

TAG_COUNT=$(exec_db "SELECT COUNT(*) FROM recipes_tag;" | tr -d ' ')
echo "   Тегов в базе: $TAG_COUNT"
echo ""

echo "5. Создание суперпользователя..."

# Удаляем старого суперпользователя если есть
exec_db "DELETE FROM users_user WHERE email='admin@example.com';" 2>/dev/null || true

exec_backend python manage.py shell << EOF
from django.contrib.auth import get_user_model

User = get_user_model()

User.objects.create_superuser(
    email='admin@example.com',
    username='admin',
    password='admin123',
    first_name='Admin',
    last_name='User'
)
print('✅ Суперпользователь создан')
EOF

echo ""

echo "6. Создание тестовых пользователей..."

exec_backend python manage.py shell << EOF
from django.contrib.auth import get_user_model

User = get_user_model()

# Удаляем старых тестовых пользователей
User.objects.filter(email__in=['author1@example.com', 'author2@example.com']).delete()

# Создаем первого пользователя
user1 = User.objects.create_user(
    email='author1@example.com',
    username='author1',
    password='password123',
    first_name='Иван',
    last_name='Петров'
)
print('✅ Пользователь author1 создан')

# Создаем второго пользователя
user2 = User.objects.create_user(
    email='author2@example.com',
    username='author2',
    password='password123',
    first_name='Мария',
    last_name='Иванова'
)
print('✅ Пользователь author2 создан')
EOF

USER_COUNT=$(exec_db "SELECT COUNT(*) FROM users_user;" | tr -d ' ')
echo "   Пользователей в базе: $USER_COUNT"
echo ""

echo "7. Создание тестовых рецептов..."

# Создаем тестовое изображение (1x1 прозрачный PNG)
TEST_IMAGE="iVBORw0KGgoAAAANSUhEUgAAAAEAAAABCAYAAAAfFcSJAAAADUlEQVR42mNk+M9QDwADhgGAWjR9awAAAABJRU5ErkJggg=="

exec_backend python manage.py shell << EOF
import base64
from django.core.files.base import ContentFile
from django.contrib.auth import get_user_model
from recipes.models import Recipe, Ingredient, Tag, IngredientInRecipe
import os

User = get_user_model()

# Получаем пользователей
try:
    author1 = User.objects.get(email='author1@example.com')
    author2 = User.objects.get(email='author2@example.com')
except User.DoesNotExist:
    print('❌ Пользователи не найдены')
    exit()

# Получаем теги
tags = {tag.slug: tag for tag in Tag.objects.all()}
if not tags:
    print('❌ Теги не найдены')
    exit()

# Получаем ингредиенты
ingredients = list(Ingredient.objects.all())
if len(ingredients) < 10:
    print('❌ Недостаточно ингредиентов')
    exit()

# Создаем изображение
def get_test_image():
    return ContentFile(
        base64.b64decode('$TEST_IMAGE'),
        name='test.png'
    )

# Рецепты для первого пользователя
recipes_for_user1 = [
    {
        'name': 'Борщ',
        'text': 'Классический украинский борщ с мясом и свеклой',
        'cooking_time': 90,
        'tags': ['soup', 'dinner'],
        'ingredients': [
            (ingredients[0], 500),  # Свекла
            (ingredients[1], 300),  # Картофель
            (ingredients[2], 200),  # Морковь
            (ingredients[3], 300),  # Лук
            (ingredients[4], 400),  # Мясо
        ]
    },
    {
        'name': 'Салат Цезарь',
        'text': 'Популярный салат с курицей и соусом',
        'cooking_time': 30,
        'tags': ['salad', 'lunch'],
        'ingredients': [
            (ingredients[5], 300),  # Курица
            (ingredients[6], 200),  # Салат
            (ingredients[7], 100),  # Сухарики
            (ingredients[8], 100),  # Сыр
        ]
    },
    {
        'name': 'Омлет',
        'text': 'Пышный омлет с овощами',
        'cooking_time': 15,
        'tags': ['breakfast'],
        'ingredients': [
            (ingredients[9], 4),    # Яйца
            (ingredients[10], 100), # Молоко
            (ingredients[11], 100), # Помидоры
            (ingredients[12], 50),  # Зелень
        ]
    },
    {
        'name': 'Шарлотка',
        'text': 'Яблочный пирог',
        'cooking_time': 60,
        'tags': ['dessert', 'baking'],
        'ingredients': [
            (ingredients[13], 200), # Мука
            (ingredients[14], 200), # Сахар
            (ingredients[15], 3),   # Яйца
            (ingredients[16], 400), # Яблоки
        ]
    },
]

# Рецепты для второго пользователя
recipes_for_user2 = [
    {
        'name': 'Гречка по-купечески',
        'text': 'Гречка с мясом и овощами',
        'cooking_time': 50,
        'tags': ['dinner'],
        'ingredients': [
            (ingredients[0], 300),  # Гречка
            (ingredients[1], 400),  # Мясо
            (ingredients[2], 200),  # Лук
            (ingredients[3], 200),  # Морковь
        ]
    },
    {
        'name': 'Панкейки',
        'text': 'Американские блинчики',
        'cooking_time': 25,
        'tags': ['breakfast', 'dessert'],
        'ingredients': [
            (ingredients[4], 200),  # Мука
            (ingredients[5], 50),   # Сахар
            (ingredients[6], 2),    # Яйца
            (ingredients[7], 200),  # Молоко
            (ingredients[8], 50),   # Масло
        ]
    },
    {
        'name': 'Куриный суп',
        'text': 'Легкий куриный суп с лапшой',
        'cooking_time': 60,
        'tags': ['soup', 'lunch'],
        'ingredients': [
            (ingredients[9], 400),  # Курица
            (ingredients[10], 200), # Морковь
            (ingredients[11], 200), # Лук
            (ingredients[12], 300), # Картофель
            (ingredients[13], 100), # Лапша
        ]
    },
]

# Функция создания рецепта
def create_recipe(author, recipe_data):
    recipe = Recipe.objects.create(
        author=author,
        name=recipe_data['name'],
        text=recipe_data['text'],
        cooking_time=recipe_data['cooking_time'],
        image=get_test_image()
    )
    
    # Добавляем теги
    for slug in recipe_data['tags']:
        if slug in tags:
            recipe.tags.add(tags[slug])
    
    # Добавляем ингредиенты
    for ingredient, amount in recipe_data['ingredients']:
        IngredientInRecipe.objects.create(
            recipe=recipe,
            ingredient=ingredient,
            amount=amount
        )
    
    print(f'  ✅ {recipe.name}')

# Создаем рецепты
print('Рецепты author1:')
for recipe_data in recipes_for_user1:
    create_recipe(author1, recipe_data)

print('\nРецепты author2:')
for recipe_data in recipes_for_user2:
    create_recipe(author2, recipe_data)

print(f'\n✅ Всего создано рецептов: {Recipe.objects.count()}')
EOF

RECIPE_COUNT=$(exec_db "SELECT COUNT(*) FROM recipes_recipe;" | tr -d ' ')
echo "   Рецептов в базе: $RECIPE_COUNT"
echo ""

echo "====================================="
echo "✅ ПОЛНАЯ ПЕРЕЗАГРУЗКА ЗАВЕРШЕНА"
echo "====================================="
echo "Итоги:"
echo "- Ингредиентов: $(exec_db "SELECT COUNT(*) FROM recipes_ingredient;" | tr -d ' ')"
echo "- Тегов: $(exec_db "SELECT COUNT(*) FROM recipes_tag;" | tr -d ' ')"
echo "- Пользователей: $(exec_db "SELECT COUNT(*) FROM users_user;" | tr -d ' ')"
echo "- Рецептов: $(exec_db "SELECT COUNT(*) FROM recipes_recipe;" | tr -d ' ')"