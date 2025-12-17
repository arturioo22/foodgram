from django.contrib.auth.backends import ModelBackend
from django.contrib.auth import get_user_model
from django.db.models import Q

User = get_user_model()

from django.contrib.auth.backends import ModelBackend
from django.contrib.auth import get_user_model
from django.db.models import Q

User = get_user_model()


class EmailOrUsernameModelBackend(ModelBackend):
    """
    Кастомный бэкенд для аутентификации по email или username.
    """

    def authenticate(self, request, username=None, password=None, **kwargs):
        if username is None:
            username = kwargs.get(User.USERNAME_FIELD)

        try:
            user = User.objects.get(
                Q(email=username) | Q(username=username)
            )
        except User.DoesNotExist:
            User().set_password(password)
            return None
        except User.MultipleObjectsReturned:
            user = User.objects.filter(
                Q(email=username) | Q(username=username)
            ).first()

        if (
            user
            and user.check_password(password)
            and self.user_can_authenticate(user)
        ):
            return user
        return None
