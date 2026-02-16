INGREDIENT_NAME_MAX_LENGTH = 128
MEASUREMENT_UNIT_MAX_LENGTH = 64
TAG_NAME_MAX_LENGTH = 32
TAG_COLOR_MAX_LENGTH = 7
TAG_SLUG_MAX_LENGTH = 32
RECIPE_NAME_MAX_LENGTH = 256
RECIPE_TEXT_MAX_LENGTH = 2000

# Ограничения для числовых полей
MIN_AMOUNT = 1
MAX_AMOUNT = 10000
MIN_COOKING_TIME = 1
MAX_COOKING_TIME = 1440

# Сообщения об ошибках
AMOUNT_VALIDATION_ERROR = (
    f'Количество должно быть не менее {MIN_AMOUNT} '
    f'и не более {MAX_AMOUNT}.'
)

COOKING_TIME_VALIDATION_ERROR = (
    f'Время приготовления должно быть не менее '
    f'{MIN_COOKING_TIME} минуты и не более '
    f'{MAX_COOKING_TIME} минут (24 часа).'
)
