# Скрипт для первоначальной настройки базы данных.
# Загружаем ингредиенты, создаем теги и суперпользователя.

set -e

exec_backend() {
    docker-compose -f docker-compose.production.yml exec -T backend "$@"
}

exec_db() {
    docker-compose -f docker-compose.production.yml exec -T db psql -U foodgram_user -d foodgram -t -c "$1"
}

echo "Настройка базы данных..."

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

TAG_COUNT=$(exec_db "SELECT COUNT(*) FROM recipes_tag;" | tr -d ' ' || echo "0")

if [ "$TAG_COUNT" = "0" ]; then
    echo "Создание тегов..."

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

print(f'Создано {Tag.objects.count()} тегов')
EOF

    NEW_COUNT=$(exec_db "SELECT COUNT(*) FROM recipes_tag;" | tr -d ' ')
    echo "Создано $NEW_COUNT тегов"
else
    echo "Теги уже загружены ($TAG_COUNT шт.)"
fi

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

echo "Настройка базы данных завершена успешно!"