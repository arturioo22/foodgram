echo "Создание тестовых рецептов..."

exec_backend python manage.py shell << EOF
from django.contrib.auth import get_user_model
from recipes.models import Recipe, Ingredient, Tag, IngredientInRecipe
from django.utils import timezone
import random

User = get_user_model()

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

# Функция для создания рецепта
def create_recipe(author, recipe_data):
    # Явно указываем все поля, включая pub_date и updated
    recipe = Recipe.objects.create(
        author=author,
        name=recipe_data['name'],
        text=recipe_data['text'],
        cooking_time=recipe_data['cooking_time'],
        pub_date=timezone.now(),  # Явно задаем дату публикации
        # updated заполнится автоматически благодаря auto_now=True
    )
    
    # Добавляем теги
    for tag in recipe_data['tags']:
        recipe.tags.add(tag)
    
    # Добавляем ингредиенты
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