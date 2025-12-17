from django.apps import AppConfig


class UsersConfig(AppConfig):
    default_auto_field = 'django.db.models.BigAutoField'
    name = 'users'
    verbose_name = 'Пользователи'

    def ready(self):
        """Импортируем сигналы при запуске приложения."""
        try:
            import users.signals
        except ImportError:
            pass
