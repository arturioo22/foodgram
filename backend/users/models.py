from django.contrib.auth.models import AbstractUser, BaseUserManager
from django.core.exceptions import ValidationError
from django.core.validators import RegexValidator
from django.db import models
from django.db.models import Q
from django.utils.translation import gettext_lazy as _


class CustomUserManager(BaseUserManager):
    """Кастомный менеджер поддержки аутентификации по email."""

    use_in_migrations = True

    def get_by_natural_key(self, username):
        return self.get(
            Q(username=username) | Q(email=username)
        )

    def _create_user(self, email, password, **extra_fields):
        """Создает и сохраняет пользователя с email и паролем."""
        if not email:
            raise ValueError('Email должен быть указан')
        email = self.normalize_email(email)
        user = self.model(email=email, **extra_fields)
        user.set_password(password)
        user.save(using=self._db)
        return user

    def create_user(self, email, password=None, **extra_fields):
        """Создает обычного пользователя."""
        extra_fields.setdefault('is_staff', False)
        extra_fields.setdefault('is_superuser', False)
        return self._create_user(email, password, **extra_fields)

    def create_superuser(self, email, password, **extra_fields):
        """Создает суперпользователя."""
        extra_fields.setdefault('is_staff', True)
        extra_fields.setdefault('is_superuser', True)
        extra_fields.setdefault('is_active', True)

        if extra_fields.get('is_staff') is not True:
            raise ValueError('Суперпользователь должен иметь is_staff=True.')
        if extra_fields.get('is_superuser') is not True:
            raise ValueError(
                'Суперпользователь должен иметь is_superuser=True.')

        return self._create_user(email, password, **extra_fields)


class User(AbstractUser):
    """
    Кастомная модель пользователя.
    Расширяет стандартную модель Django AbstractUser.
    """

    objects = CustomUserManager()

    username_validator = RegexValidator(
        regex=r'^[\w.@+-]+\Z',
        message=_(
            'Имя пользователя может содержать '
            'только буквы, цифры и @/./+/-/_')
    )

    email = models.EmailField(
        _('Адрес электронной почты'),
        max_length=254,
        unique=True,
        blank=False,
        null=False,
        help_text=_('Обязательное поле. Введите действующий email адрес.')
    )

    username = models.CharField(
        _('Имя пользователя'),
        max_length=150,
        unique=True,
        validators=[username_validator],
        help_text=_(
            'Обязательное поле. Не более 150 символов. '
            'Только буквы, цифры и @/./+/-/_.'
        ),
        error_messages={
            'unique': _('Пользователь с таким именем уже существует.'),
        },
    )

    first_name = models.CharField(
        _('Имя'),
        max_length=150,
        blank=False,
        null=False,
        help_text=_('Введите ваше имя (обязательно).')
    )

    last_name = models.CharField(
        _('Фамилия'),
        max_length=150,
        blank=False,
        null=False,
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
                violation_error_message=_('Нельзя подписаться на самого себя.')
            )
        ]

    def __str__(self):
        return f'{self.user} подписан на {self.author}'

    def clean(self):
        """Дополнительная валидация на уровне модели."""

        if self.user == self.author:
            raise ValidationError(_('Нельзя подписаться на самого себя.'))

        super().clean()

    def save(self, *args, **kwargs):
        """Переопределяем save для вызова full_clean."""
        self.full_clean()
        super().save(*args, **kwargs)
