from django.contrib.auth.models import AbstractUser
from django.core.exceptions import ValidationError
from django.core.validators import RegexValidator
from django.db import models
from django.utils.translation import gettext_lazy as _

from .constants import (
    EMAIL_MAX_LENGTH, USERNAME_MAX_LENGTH, NAME_MAX_LENGTH,
    USERNAME_REGEX, USERNAME_VALIDATION_MESSAGE,
    USERNAME_UNIQUE_ERROR, SELF_FOLLOW_ERROR
)
from .managers import CustomUserManager


class User(AbstractUser):
    """
    Кастомная модель пользователя.

    Расширяет стандартную модель Django AbstractUser.
    Использует email в качестве основного идентификатора для аутентификации.
    """

    objects = CustomUserManager()

    username_validator = RegexValidator(
        regex=USERNAME_REGEX,
        message=_(USERNAME_VALIDATION_MESSAGE)
    )

    email = models.EmailField(
        _('Адрес электронной почты'),
        max_length=EMAIL_MAX_LENGTH,
        unique=True,
        help_text=_('Обязательное поле. Введите действующий email адрес.')
    )

    username = models.CharField(
        _('Имя пользователя'),
        max_length=USERNAME_MAX_LENGTH,
        unique=True,
        validators=[username_validator],
        help_text=_(
            f'Обязательное поле. Не более {USERNAME_MAX_LENGTH} символов. '
            'Только буквы, цифры и @/./+/-/_.'
        ),
        error_messages={
            'unique': _(USERNAME_UNIQUE_ERROR),
        },
    )

    first_name = models.CharField(
        _('Имя'),
        max_length=NAME_MAX_LENGTH,
        help_text=_('Введите ваше имя (обязательно).')
    )

    last_name = models.CharField(
        _('Фамилия'),
        max_length=NAME_MAX_LENGTH,
        help_text=_('Введите вашу фамилию (обязательно).')
    )

    avatar = models.ImageField(
        _('Аватар'),
        upload_to='avatars/',
        blank=True,
        null=True,
        help_text=_('Загрузите изображение для аватара (необязательно).')
    )

    date_joined = models.DateTimeField(
        _('Дата регистрации'),
        auto_now_add=True
    )

    USERNAME_FIELD = 'email'
    REQUIRED_FIELDS = ['username', 'first_name', 'last_name']

    class Meta:
        verbose_name = _('Пользователь')
        verbose_name_plural = _('Пользователи')
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
        verbose_name=_('Подписчик')
    )

    author = models.ForeignKey(
        User,
        on_delete=models.CASCADE,
        related_name='following',
        verbose_name=_('Автор')
    )

    created = models.DateTimeField(
        _('Дата подписки'),
        auto_now_add=True
    )

    class Meta:
        verbose_name = _('Подписка')
        verbose_name_plural = _('Подписки')
        ordering = ['-created']
        constraints = [
            models.UniqueConstraint(
                fields=['user', 'author'],
                name='unique_follow'
            ),
            models.CheckConstraint(
                check=~models.Q(user=models.F('author')),
                name='prevent_self_follow',
                violation_error_message=_(SELF_FOLLOW_ERROR)
            )
        ]

    def __str__(self):
        return f'{self.user} подписан на {self.author}'

    def clean(self):
        """Дополнительная валидация на уровне модели."""

        if self.user == self.author:
            raise ValidationError(_(SELF_FOLLOW_ERROR))

        super().clean()

    def save(self, *args, **kwargs):
        """Переопределяем save для вызова full_clean."""
        self.full_clean()
        super().save(*args, **kwargs)
