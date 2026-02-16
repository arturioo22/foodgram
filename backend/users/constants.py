# Длины полей
EMAIL_MAX_LENGTH = 254
USERNAME_MAX_LENGTH = 150
NAME_MAX_LENGTH = 150

# Регулярное выражение для валидации username
USERNAME_REGEX = r'^[\w.@+-]+\Z'

# Сообщения об ошибках
USERNAME_VALIDATION_MESSAGE = (
    'Имя пользователя может содержать '
    'только буквы, цифры и @/./+/-/_'
)
USERNAME_UNIQUE_ERROR = 'Пользователь с таким именем уже существует.'
EMAIL_UNIQUE_ERROR = 'Пользователь с таким email уже существует.'
SELF_FOLLOW_ERROR = 'Нельзя подписаться на самого себя.'
