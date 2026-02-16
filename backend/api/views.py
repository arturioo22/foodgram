from django.db.models import Sum
from django.http import FileResponse, Http404
from django.shortcuts import get_object_or_404
from django.urls import reverse

from django_filters.rest_framework import DjangoFilterBackend

from rest_framework import status, viewsets
from rest_framework.decorators import action
from rest_framework.permissions import (
    AllowAny, IsAuthenticated, IsAuthenticatedOrReadOnly
)
from rest_framework.response import Response
from rest_framework.viewsets import ReadOnlyModelViewSet

from djoser.views import UserViewSet as DjoserUserViewSet

from recipes.models import (
    Favorite, Ingredient, IngredientInRecipe, Recipe, ShoppingCart, Tag
)
from users.models import Follow, User

from .filters import IngredientFilter, RecipeFilter
from .pagination import Pagination
from .serializers import (
    IngredientSerializer, RecipeReadSerializer,
    RecipeWriteSerializer, ShortRecipeSerializer, SubscriptionSerializer,
    TagSerializer, UserSerializer
)


class UserViewSet(DjoserUserViewSet):
    """Вьюсет для пользователей."""

    pagination_class = Pagination

    def get_serializer_class(self):
        if self.action == 'set_password':
            return super().get_serializer_class()
        return UserSerializer

    @action(
        detail=False,
        methods=['put', 'delete'],
        permission_classes=[IsAuthenticated],
        url_path='avatar'
    )
    def avatar(self, request):
        """Управление аватаром пользователя."""
        user = request.user

        if request.method == 'PUT':
            if 'avatar' not in request.data:
                return Response(
                    {'avatar': ['Это поле обязательно.']},
                    status=status.HTTP_400_BAD_REQUEST
                )

            serializer = UserSerializer(
                user,
                data={'avatar': request.data.get('avatar')},
                partial=True,
                context={'request': request}
            )

            if serializer.is_valid():
                serializer.save()
                user.refresh_from_db()
                if user.avatar:
                    return Response(
                        {'avatar': request.build_absolute_uri(
                            user.avatar.url)},
                        status=status.HTTP_200_OK
                    )
                return Response(
                    {'avatar': None},
                    status=status.HTTP_200_OK
                )

            return Response(
                serializer.errors, status=status.HTTP_400_BAD_REQUEST)

        elif request.method == 'DELETE':
            if user.avatar:
                user.avatar.delete(save=False)
            user.avatar = None
            user.save()
            return Response(status=status.HTTP_204_NO_CONTENT)

    @action(
        detail=False,
        methods=['get'],
        permission_classes=[IsAuthenticated],
        url_path='subscriptions'
    )
    def subscriptions(self, request):
        """Получить мои подписки."""
        user = request.user
        subscriptions = User.objects.filter(following__user=user)
        page = self.paginate_queryset(subscriptions)
        serializer = SubscriptionSerializer(
            page, many=True, context={'request': request}
        )
        return self.get_paginated_response(serializer.data)

    @action(
        detail=True,
        methods=['post', 'delete'],
        permission_classes=[IsAuthenticated]
    )
    def subscribe(self, request, pk=None):
        """Подписаться/отписаться на автора."""
        author = get_object_or_404(User, pk=pk)
        user = request.user

        if user == author:
            return Response(
                {'errors': 'Нельзя подписаться на самого себя'},
                status=status.HTTP_400_BAD_REQUEST
            )

        if request.method == 'POST':
            if Follow.objects.filter(user=user, author=author).exists():
                return Response(
                    {'errors': 'Вы уже подписаны на этого автора'},
                    status=status.HTTP_400_BAD_REQUEST
                )

            Follow.objects.create(user=user, author=author)
            serializer = SubscriptionSerializer(
                author, context={'request': request}
            )
            return Response(serializer.data, status=status.HTTP_201_CREATED)

        # DELETE
        deleted_count, _ = Follow.objects.filter(
            user=user, author=author
        ).delete()

        if deleted_count == 0:
            return Response(
                {'errors': 'Вы не подписаны на этого автора'},
                status=status.HTTP_400_BAD_REQUEST
            )

        return Response(status=status.HTTP_204_NO_CONTENT)


class RecipeViewSet(viewsets.ModelViewSet):
    """Вьюсет для рецептов."""

    queryset = Recipe.objects.all()
    permission_classes = [IsAuthenticatedOrReadOnly]
    filter_backends = [DjangoFilterBackend]
    filterset_class = RecipeFilter
    pagination_class = Pagination

    def get_serializer_class(self):
        if self.action in ('create', 'update', 'partial_update'):
            return RecipeWriteSerializer
        return RecipeReadSerializer

    def perform_create(self, serializer):
        serializer.save(author=self.request.user)

    def update(self, request, *args, **kwargs):
        """Общий метод для PUT и PATCH."""
        partial = kwargs.pop('partial', False)

        try:
            instance = self.get_object()
        except Http404:
            return Response(
                {'detail': 'Страница не найдена.'},
                status=status.HTTP_404_NOT_FOUND
            )

        if instance.author != request.user:
            return Response(
                {'detail': 'Недостаточно прав для данного действия.'},
                status=status.HTTP_403_FORBIDDEN
            )

        serializer = self.get_serializer(
            instance,
            data=request.data,
            partial=partial
        )
        serializer.is_valid(raise_exception=True)
        self.perform_update(serializer)

        return Response(serializer.data)

    def destroy(self, request, *args, **kwargs):
        """DELETE - удаление."""
        try:
            instance = self.get_object()
        except Http404:
            return Response(
                {'detail': 'Страница не найдена.'},
                status=status.HTTP_404_NOT_FOUND
            )

        if instance.author != request.user:
            return Response(
                {'detail': 'Недостаточно прав для данного действия'},
                status=status.HTTP_403_FORBIDDEN
            )

        self.perform_destroy(instance)
        return Response(status=status.HTTP_204_NO_CONTENT)

    @action(
        detail=True,
        methods=['post', 'delete'],
        permission_classes=[IsAuthenticated]
    )
    def favorite(self, request, pk=None):
        """Добавить/удалить рецепт в избранное."""
        return self._add_remove_relation(Favorite, request, pk)

    @action(
        detail=True,
        methods=['post', 'delete'],
        permission_classes=[IsAuthenticated]
    )
    def shopping_cart(self, request, pk=None):
        """Добавить/удалить рецепт в список покупок."""
        return self._add_remove_relation(ShoppingCart, request, pk)

    def _add_remove_relation(self, model, request, pk):
        """Общий метод для добавления/удаления отношений."""
        recipe = get_object_or_404(Recipe, pk=pk)
        user = request.user

        if request.method == 'POST':
            if model.objects.filter(user=user, recipe=recipe).exists():
                return Response(
                    {'errors': 'Рецепт уже добавлен'},
                    status=status.HTTP_400_BAD_REQUEST
                )

            try:
                model.objects.create(user=user, recipe=recipe)
                serializer = ShortRecipeSerializer(
                    recipe,
                    context={'request': request}
                )
                return Response(
                    serializer.data, status=status.HTTP_201_CREATED
                )
            except Exception as e:
                return Response(
                    {'errors': str(e)},
                    status=status.HTTP_400_BAD_REQUEST
                )

        # DELETE
        deleted_count, _ = model.objects.filter(
            user=user, recipe=recipe
        ).delete()

        if deleted_count == 0:
            return Response(
                {'errors': 'Рецепт не найден'},
                status=status.HTTP_400_BAD_REQUEST
            )

        return Response(status=status.HTTP_204_NO_CONTENT)

    def _generate_shopping_list_text(self, ingredients):
        """Генерация текста списка покупок."""
        shopping_list = "Список покупок:\n\n"
        for ingredient in ingredients:
            name = ingredient['ingredient__name']
            unit = ingredient['ingredient__measurement_unit']
            amount = ingredient['total_amount']
            shopping_list += f"{name} ({unit}) - {amount}\n"
        return shopping_list

    @action(
        detail=False,
        methods=['get'],
        permission_classes=[IsAuthenticated]
    )
    def download_shopping_cart(self, request):
        """Скачать список покупок."""
        user = request.user

        ingredients = IngredientInRecipe.objects.filter(
            recipe__shopping_cart__user=user
        ).values(
            'ingredient__name',
            'ingredient__measurement_unit'
        ).annotate(
            total_amount=Sum('amount')
        ).order_by('ingredient__name')

        if not ingredients.exists():
            return Response(
                {'errors': 'Список покупок пуст'},
                status=status.HTTP_400_BAD_REQUEST
            )

        shopping_list_text = self._generate_shopping_list_text(ingredients)

        response = FileResponse(
            shopping_list_text.encode('utf-8'),
            content_type='text/plain; charset=utf-8',
            as_attachment=True,
            filename='shopping-list.txt'
        )
        return response

    @action(
        detail=True,
        methods=['get'],
        url_path='get-link'
    )
    def get_link(self, request, pk=None):
        """Получить короткую ссылку на рецепт."""
        self.get_object()
        link = request.build_absolute_uri(
            reverse('shortlink-redirect', args=[pk])
        )
        return Response({'short-link': link})


class IngredientViewSet(ReadOnlyModelViewSet):
    """Вьюсет для ингредиентов (только чтение)."""

    queryset = Ingredient.objects.all()
    serializer_class = IngredientSerializer
    filterset_class = IngredientFilter
    filter_backends = [DjangoFilterBackend]
    pagination_class = None
    permission_classes = [AllowAny]


class TagViewSet(ReadOnlyModelViewSet):
    """Вьюсет для тегов (только чтение)."""

    queryset = Tag.objects.all()
    serializer_class = TagSerializer
    pagination_class = None
    permission_classes = [AllowAny]
