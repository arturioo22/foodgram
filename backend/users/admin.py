from django.contrib import admin
from django.contrib.auth.admin import UserAdmin as DjangoUserAdmin
from django.utils.translation import gettext_lazy as _

from .models import Follow, User


@admin.register(User)
class UserAdmin(DjangoUserAdmin):
    """Админка для пользователей с кастомными настройками."""

    list_display = ('email', 'username', 'first_name',
                    'last_name', 'is_staff', 'is_active')
    list_filter = ('is_staff', 'is_superuser', 'is_active', 'date_joined')
    search_fields = ('email', 'username', 'first_name', 'last_name')
    ordering = ('email',)
    readonly_fields = ('last_login', 'date_joined')

    fieldsets = (
        (None, {'fields': ('email', 'password')}),
        (_('Personal info'), {'fields': ('username', 'first_name',
                                         'last_name', 'avatar')}),
        (_('Permissions'), {
            'fields': ('is_active', 'is_staff', 'is_superuser',
                       'groups', 'user_permissions'),
        }),
        (_('Important dates'), {'fields': ('last_login', 'date_joined')}),
    )

    add_fieldsets = (
        (None, {
            'classes': ('wide',),
            'fields': ('email', 'username', 'first_name',
                       'last_name', 'password1', 'password2'),
        }),
    )

    def get_form(self, request, obj=None, **kwargs):
        """Переопределяем форму для корректного отображения
        email как USERNAME_FIELD."""
        form = super().get_form(request, obj, **kwargs)
        if 'username' in form.base_fields:
            form.base_fields['username'].required = True
        return form


@admin.register(Follow)
class FollowAdmin(admin.ModelAdmin):
    """Админка для подписок."""

    list_display = ('user', 'author', 'created')
    list_filter = ('created',)
    search_fields = ('user__username', 'user__email',
                     'author__username', 'author__email')
    readonly_fields = ('created',)

    fieldsets = (
        (_('Основная информация'), {
            'fields': ('user', 'author')
        }),
        (_('Дата'), {
            'fields': ('created',)
        }),
    )
