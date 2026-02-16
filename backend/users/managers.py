from django.contrib.auth.models import BaseUserManager
from django.db.models import Q


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
