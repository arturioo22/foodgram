PAGE_SIZE = 6

# Константы для валидации
MIN_AMOUNT = 1
MAX_AMOUNT = 32000
MIN_COOKING_TIME = 1
MAX_COOKING_TIME = 32000
MAX_NAME_LENGTH = 200
MAX_TEXT_LENGTH = 2000

# Сообщения об ошибках
ERROR_MESSAGES = {
    'required': 'Это поле обязательно.',
    'blank': 'Это поле не может быть пустым.',
    'min_amount': (
        f'Количество должно быть не менее {MIN_AMOUNT}.'
    ),
    'max_amount': (
        f'Количество должно быть не более {MAX_AMOUNT}.'
    ),
    'min_time': (
        f'Время приготовления должно быть не менее '
        f'{MIN_COOKING_TIME} минуты.'
    ),
    'max_time': (
        f'Время приготовления должно быть не более '
        f'{MAX_COOKING_TIME} минут.'
    ),
    'duplicate_ingredients': 'Ингредиенты не должны повторяться.',
    'duplicate_tags': 'Теги не должны повторяться.',
    'at_least_one_ingredient': 'Добавьте хотя бы один ингредиент.',
    'at_least_one_tag': 'Добавьте хотя бы один тег.',
}
