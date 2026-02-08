from django.contrib.auth.models import AbstractUser, BaseUserManager
from django.db import models
from django.core.validators import RegexValidator
from django.db.models import Q

class CustomUserManager(BaseUserManager):
    """Кастомный менеджер поддержки аутентификации по email."""

    def get_by_natural_key(self, username):
        return self.get(
            Q(username=username) |
            Q(email=username)
        )


class User(AbstractUser):
    """
    Кастомная модель пользователя.
    Расширяет стандартную модель Django AbstractUser.
    """

    objects = CustomUserManager()

    username_validator = RegexValidator(
        regex=r'^[\w.@+-]+\Z',
        message=(
            'Имя пользователя может содержать '
            'только буквы, цифры и @/./+/-/_')
    )

    email = models.EmailField(
        'Адрес электронной почты',
        max_length=254,
        unique=True,
        blank=False,
        null=False,
        help_text='Обязательное поле. Введите действующий email адрес.'
    )

    username = models.CharField(
        'Имя пользователя',
        max_length=150,
        unique=True,
        validators=[username_validator],
        help_text=(
            'Обязательное поле. Не более 150 символов. '
            'Только буквы, цифры и @/./+/-/_.'
        ),
        error_messages={
            'unique': 'Пользователь с таким именем уже существует.',
        },
    )

    first_name = models.CharField(
        'Имя',
        max_length=150,
        blank=False,
        null=False,
        help_text='Введите ваше имя (обязательно).'
    )

    last_name = models.CharField(
        'Фамилия',
        max_length=150,
        blank=False,
        null=False,
        help_text='Введите вашу фамилию (обязательно).'
    )

    avatar = models.ImageField(
        'Аватар',
        upload_to='avatars/',
        blank=True,
        null=True,
        help_text='Загрузите изображение для аватара (необязательно).'
    )

    date_joined = models.DateTimeField(
        'Дата регистрации',
        auto_now_add=True
    )

    class Meta:
        verbose_name = 'Пользователь'
        verbose_name_plural = 'Пользователи'
        ordering = ['username']
        constraints = [
            models.UniqueConstraint(
                fields=['email'],
                name='unique_email'
            )
        ]

    def __str__(self):
        return self.username

    def get_full_name(self):
        """Возвращает полное имя пользователя."""
        return f'{self.first_name} {self.last_name}'

    def get_short_name(self):
        """Возвращает короткое имя пользователя (имя)."""
        return self.first_name

    @property
    def is_admin(self):
        """Проверяет, является ли пользователь администратором."""
        return self.is_staff or self.is_superuser


class Follow(models.Model):
    """
    Модель для подписок пользователей друг на друга.
    """

    user = models.ForeignKey(
        User,
        on_delete=models.CASCADE,
        related_name='follower',
        verbose_name='Подписчик'
    )

    author = models.ForeignKey(
        User,
        on_delete=models.CASCADE,
        related_name='following',
        verbose_name='Автор'
    )

    created = models.DateTimeField(
        'Дата подписки',
        auto_now_add=True
    )

    class Meta:
        verbose_name = 'Подписка'
        verbose_name_plural = 'Подписки'
        ordering = ['-created']
        constraints = [
            models.UniqueConstraint(
                fields=['user', 'author'],
                name='unique_follow'
            ),
            models.CheckConstraint(
                check=~models.Q(user=models.F('author')),
                name='prevent_self_follow',
                violation_error_message='Нельзя подписаться на самого себя.'
            )
        ]

    def __str__(self):
        return f'{self.user} подписан на {self.author}'

    def clean(self):
        """Дополнительная валидация на уровне модели."""

        from django.core.exceptions import ValidationError

        if self.user == self.author:
            raise ValidationError('Нельзя подписаться на самого себя.')

        super().clean()

    def save(self, *args, **kwargs):
        """Переопределяем save для вызова full_clean."""
        self.full_clean()
        super().save(*args, **kwargs)
