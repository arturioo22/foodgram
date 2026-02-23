from rest_framework import permissions
from rest_framework.permissions import BasePermission


class IsAuthorOrReadOnly(permissions.BasePermission):
    """
    Проверка прав доступа для автора рецепта.

    Разрешает изменение только автору объекта.
    Остальным пользователям доступно только чтение.
    """

    def has_object_permission(self, request, view, obj):
        return (
            request.method in permissions.SAFE_METHODS
            or obj.author == request.user
        )
