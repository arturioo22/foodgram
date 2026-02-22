# Скрипт для первоначальной настройки базы данных.
# Загружаем ингредиенты, создаем теги, суперпользователя и тестовые рецепты.

set -e

exec_backend() {
    docker-compose -f docker-compose.production.yml exec -T backend "$@"
}

exec_db() {
    docker-compose -f docker-compose.production.yml exec -T db psql -U foodgram_user -d foodgram -t -c "$1"
}

echo "Настройка базы данных..."

# Загрузка ингредиентов
ING_COUNT=$(exec_db "SELECT COUNT(*) FROM recipes_ingredient;" | tr -d ' ' || echo "0")

if [ "$ING_COUNT" = "0" ] || [ "$ING_COUNT" -lt "1000" ]; then
    echo "Загрузка ингредиентов в базу данных..."

    docker cp data/ingredients.json foodgram_backend_prod:/app/data/ingredients.json

    exec_backend python -c "
import json

with open('/app/data/ingredients.json', 'r', encoding='utf-8') as f:
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

print(f'Конвертировано {len(fixture)} ингредиентов')
"

    exec_backend python manage.py loaddata /app/data/ingredients_fixture.json

    NEW_COUNT=$(exec_db "SELECT COUNT(*) FROM recipes_ingredient;" | tr -d ' ')
    echo "Загружено $NEW_COUNT ингредиентов"
else
    echo "Ингредиенты уже загружены ($ING_COUNT шт.)"
fi

# Создание тегов (исправлено: убран color)
TAG_COUNT=$(exec_db "SELECT COUNT(*) FROM recipes_tag;" | tr -d ' ' || echo "0")

if [ "$TAG_COUNT" = "0" ]; then
    echo "Создание тегов..."

    exec_backend python manage.py shell << EOF
from recipes.models import Tag

tags = [
    {'name': 'Завтрак', 'slug': 'breakfast'},
    {'name': 'Обед', 'slug': 'lunch'},
    {'name': 'Ужин', 'slug': 'dinner'},
    {'name': 'Десерт', 'slug': 'dessert'},
    {'name': 'Выпечка', 'slug': 'baking'},
    {'name': 'Салат', 'slug': 'salad'},
    {'name': 'Супы', 'slug': 'soup'},
    {'name': 'Напитки', 'slug': 'drinks'},
]

for tag in tags:
    Tag.objects.get_or_create(**tag)

print(f'Создано {Tag.objects.count()} тегов')
EOF

    NEW_COUNT=$(exec_db "SELECT COUNT(*) FROM recipes_tag;" | tr -d ' ')
    echo "Создано $NEW_COUNT тегов"
else
    echo "Теги уже загружены ($TAG_COUNT шт.)"
fi

# Создание суперпользователя
SUPERUSER_EXISTS=$(exec_db "SELECT COUNT(*) FROM users_user WHERE is_superuser = true;" | tr -d ' ' || echo "0")

if [ "$SUPERUSER_EXISTS" = "0" ]; then
    echo "Создание суперпользователя..."

    exec_backend python manage.py shell << EOF
from django.contrib.auth import get_user_model

User = get_user_model()

if not User.objects.filter(is_superuser=True).exists():
    User.objects.create_superuser(
        email='admin@example.com',
        username='admin',
        password='admin123',
        first_name='Admin',
        last_name='User'
    )
    print('Суперпользователь создан')
else:
    print('Суперпользователь уже существует')
EOF

    echo "Суперпользователь создан"
else
    echo "Суперпользователь уже существует"
fi

echo "Создание тестовых пользователей..."

exec_backend python manage.py shell << EOF
from django.contrib.auth import get_user_model

User = get_user_model()

# Создаем первого пользователя
user1, created = User.objects.get_or_create(
    email='author1@example.com',
    defaults={
        'username': 'author1',
        'first_name': 'Иван',
        'last_name': 'Петров',
        'is_active': True
    }
)
if created:
    user1.set_password('password123')
    user1.save()
    print('Пользователь author1 создан')
else:
    print('Пользователь author1 уже существует')

# Создаем второго пользователя
user2, created = User.objects.get_or_create(
    email='author2@example.com',
    defaults={
        'username': 'author2',
        'first_name': 'Мария',
        'last_name': 'Иванова',
        'is_active': True
    }
)
if created:
    user2.set_password('password123')
    user2.save()
    print('Пользователь author2 создан')
else:
    print('Пользователь author2 уже существует')
EOF

echo "Создание тестовых рецептов..."

# Добавляем тестовое изображение (1x1 прозрачный PNG в base64)
TEST_IMAGE="iVBORw0KGgoAAAANSUhEUgAAAAEAAAABCAYAAAAfFcSJAAAADUlEQVR42mNk+M9QDwADhgGAWjR9awAAAABJRU5ErkJggg=="

exec_backend python manage.py shell << EOF
import base64
from django.core.files.base import ContentFile
from django.contrib.auth import get_user_model
from recipes.models import Recipe, Ingredient, Tag, IngredientInRecipe

User = get_user_model()

# Функция для создания тестового изображения
def get_test_image():
    return ContentFile(
        base64.b64decode('$TEST_IMAGE'),
        name='test.png'
    )

# Получаем пользователей
try:
    author1 = User.objects.get(email='author1@example.com')
    author2 = User.objects.get(email='author2@example.com')
except User.DoesNotExist:
    print('Пользователи не найдены')
    exit()

# Получаем теги
tags = list(Tag.objects.all())
if not tags:
    print('Теги не найдены')
    exit()

# Получаем ингредиенты
ingredients = list(Ingredient.objects.all()[:20])
if len(ingredients) < 3:
    print('Недостаточно ингредиентов')
    exit()

# Создаем рецепты для первого пользователя
recipes_for_user1 = [
    {
        'name': 'Борщ',
        'text': 'обычный борщ',
        'cooking_time': 90,
        'tags': [t for t in tags if t.slug in ['soup', 'dinner']],
        'ingredients': [
            {'ingredient': ingredients[0], 'amount': 500},
            {'ingredient': ingredients[1], 'amount': 300},
            {'ingredient': ingredients[2], 'amount': 200},
            {'ingredient': ingredients[3], 'amount': 300},
            {'ingredient': ingredients[4], 'amount': 400},
        ]
    },
    {
        'name': 'Салат',
        'text': 'салат с курицей',
        'cooking_time': 30,
        'tags': [t for t in tags if t.slug in ['salad', 'lunch']],
        'ingredients': [
            {'ingredient': ingredients[5], 'amount': 300},
            {'ingredient': ingredients[6], 'amount': 200},
            {'ingredient': ingredients[7], 'amount': 100},
            {'ingredient': ingredients[8], 'amount': 100},
        ]
    },
    {
        'name': 'Омлет',
        'text': 'Хороший завтрак',
        'cooking_time': 15,
        'tags': [t for t in tags if t.slug in ['breakfast']],
        'ingredients': [
            {'ingredient': ingredients[9], 'amount': 4},
            {'ingredient': ingredients[10], 'amount': 100},
            {'ingredient': ingredients[11], 'amount': 100},
            {'ingredient': ingredients[12], 'amount': 50},
        ]
    },
    {
        'name': 'Шарлотка',
        'text': 'яблочный пирог',
        'cooking_time': 60,
        'tags': [t for t in tags if t.slug in ['dessert', 'baking']],
        'ingredients': [
            {'ingredient': ingredients[13], 'amount': 200},
            {'ingredient': ingredients[14], 'amount': 200},
            {'ingredient': ingredients[15], 'amount': 3},
            {'ingredient': ingredients[16], 'amount': 400},
        ]
    },
]

# Создаем рецепты для второго пользователя (3 рецепта)
recipes_for_user2 = [
    {
        'name': 'Гречка',
        'text': 'обычная гречка',
        'cooking_time': 50,
        'tags': [t for t in tags if t.slug in ['dinner']],
        'ingredients': [
            {'ingredient': ingredients[0], 'amount': 300},
            {'ingredient': ingredients[1], 'amount': 400},
            {'ingredient': ingredients[2], 'amount': 200},
            {'ingredient': ingredients[3], 'amount': 200},
        ]
    },
    {
        'name': 'Блины',
        'text': 'обычные блины',
        'cooking_time': 25,
        'tags': [t for t in tags if t.slug in ['breakfast', 'dessert']],
        'ingredients': [
            {'ingredient': ingredients[4], 'amount': 200},
            {'ingredient': ingredients[5], 'amount': 50},
            {'ingredient': ingredients[6], 'amount': 2},
            {'ingredient': ingredients[7], 'amount': 200},
            {'ingredient': ingredients[8], 'amount': 50},
        ]
    },
    {
        'name': 'Куриный суп',
        'text': 'обычный куриный суп',
        'cooking_time': 60,
        'tags': [t for t in tags if t.slug in ['soup', 'lunch']],
        'ingredients': [
            {'ingredient': ingredients[9], 'amount': 400},
            {'ingredient': ingredients[10], 'amount': 200},
            {'ingredient': ingredients[11], 'amount': 200},
            {'ingredient': ingredients[12], 'amount': 300},
            {'ingredient': ingredients[13], 'amount': 100},
        ]
    },
]

def create_recipe(author, recipe_data):
    # Создаем рецепт без указания updated (оно auto_now)
    recipe = Recipe(
        author=author,
        name=recipe_data['name'],
        text=recipe_data['text'],
        cooking_time=recipe_data['cooking_time'],
        image=get_test_image()
    )
    recipe.save()  # save вызовет установку auto_now
    
    # Добавляем теги
    for tag in recipe_data['tags']:
        recipe.tags.add(tag)
    
    # Добавляем ингредиенты
    from recipes.models import IngredientInRecipe
    for ing_data in recipe_data['ingredients']:
        IngredientInRecipe.objects.create(
            recipe=recipe,
            ingredient=ing_data['ingredient'],
            amount=ing_data['amount']
        )
    
    print(f'  - Создан рецепт: {recipe.name}')
    return recipe

# Создаем рецепты для первого пользователя
print('Создание рецептов для author1:')
for recipe_data in recipes_for_user1:
    # Проверяем, существует ли уже такой рецепт
    if not Recipe.objects.filter(name=recipe_data['name'], author=author1).exists():
        create_recipe(author1, recipe_data)
    else:
        print(f'  - Рецепт "{recipe_data["name"]}" уже существует')

# Создаем рецепты для второго пользователя
print('\nСоздание рецептов для author2:')
for recipe_data in recipes_for_user2:
    if not Recipe.objects.filter(name=recipe_data['name'], author=author2).exists():
        create_recipe(author2, recipe_data)
    else:
        print(f'  - Рецепт "{recipe_data["name"]}" уже существует')

# Проверка итогов
print(f'\nВсего рецептов в базе: {Recipe.objects.count()}')
print(f'Рецептов у author1: {author1.recipes.count()}')
print(f'Рецептов у author2: {author2.recipes.count()}')
EOF

echo "Настройка базы данных завершена успешно!"
echo "Итоги:"
echo "- Ингредиентов: $(exec_db "SELECT COUNT(*) FROM recipes_ingredient;" | tr -d ' ')"
echo "- Тегов: $(exec_db "SELECT COUNT(*) FROM recipes_tag;" | tr -d ' ')"
echo "- Пользователей: $(exec_db "SELECT COUNT(*) FROM users_user;" | tr -d ' ')"
echo "- Рецептов: $(exec_db "SELECT COUNT(*) FROM recipes_recipe;" | tr -d ' ')"
