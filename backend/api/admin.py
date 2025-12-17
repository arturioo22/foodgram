from django.contrib import admin
from .models import APILog


@admin.register(APILog)
class APILogAdmin(admin.ModelAdmin):
    """Админка для логов API."""
    
    list_display = ('method', 'endpoint', 'status_code', 'user', 'created')
    list_filter = ('method', 'status_code', 'created')
    search_fields = ('endpoint', 'user__username', 'user__email')
    readonly_fields = ('created',)
    date_hierarchy = 'created'
    
    fieldsets = (
        ('Основная информация', {
            'fields': ('user', 'endpoint', 'method', 'status_code')
        }),
        ('Данные запроса', {
            'fields': ('request_data', 'response_data'),
            'classes': ('collapse',)
        }),
        ('Техническая информация', {
            'fields': ('ip_address', 'user_agent', 'duration', 'created'),
            'classes': ('collapse',)
        }),
    )
