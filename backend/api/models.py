from django.db import models
from django.utils import timezone


class APILog(models.Model):
    """
    Модель для логирования API запросов.
    """

    user = models.ForeignKey(
        'users.User',
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        verbose_name='Пользователь'
    )

    endpoint = models.CharField(
        'Эндпоинт',
        max_length=500,
        help_text='URL эндпоинта API'
    )

    method = models.CharField(
        'HTTP метод',
        max_length=10,
        help_text='HTTP метод запроса'
    )

    status_code = models.IntegerField(
        'Статус код',
        help_text='HTTP статус код ответа'
    )

    request_data = models.JSONField(
        'Данные запроса',
        null=True,
        blank=True,
        help_text='Данные отправленные в запросе'
    )

    response_data = models.TextField(
        'Данные ответа',
        null=True,
        blank=True,
        help_text='Данные полученные в ответе'
    )

    ip_address = models.GenericIPAddressField(
        'IP адрес',
        null=True,
        blank=True,
        help_text='IP адрес клиента'
    )

    user_agent = models.TextField(
        'User Agent',
        null=True,
        blank=True,
        help_text='User Agent клиента'
    )

    created = models.DateTimeField(
        'Дата запроса',
        default=timezone.now,
        db_index=True
    )

    duration = models.FloatField(
        'Длительность запроса (сек)',
        help_text='Время выполнения запроса в секундах'
    )

    class Meta:
        verbose_name = 'Лог API'
        verbose_name_plural = 'Логи API'
        ordering = ['-created']
        indexes = [
            models.Index(fields=['endpoint', 'created']),
            models.Index(fields=['user', 'created']),
            models.Index(fields=['status_code', 'created']),
        ]

    def __str__(self):
        return f'{self.method} {self.endpoint} - {self.status_code}'

    @classmethod
    def create_log(cls, **kwargs):
        """
        Создает запись лога API.
        """
        try:
            return cls.objects.create(**kwargs)
        except Exception:
            pass
