from django_filters import rest_framework as filters

from recipes.models import Ingredient, Recipe


class RecipeFilter(filters.FilterSet):
    """Фильтр для рецептов."""

    tags = filters.CharFilter(method='filter_tags')
    author = filters.NumberFilter(field_name='author_id')
    is_favorited = filters.BooleanFilter(method='filter_is_favorited')
    is_in_shopping_cart = filters.BooleanFilter(
        method='filter_is_in_shopping_cart'
    )

    class Meta:
        model = Recipe
        fields = ['author', 'tags', 'is_favorited', 'is_in_shopping_cart']

    def filter_tags(self, queryset, name, value):
        """
        Фильтрация по тегам.
        Возвращает рецепты, у которых есть хотя бы один из указанных тегов.
        """
        tags = self.request.query_params.getlist('tags')
        if tags:
            return queryset.filter(tags__slug__in=tags).distinct()
        return queryset

    def filter_is_favorited(self, queryset, name, value):
        """
        Фильтрация по избранному.
        Возвращает рецепты, добавленные в избранное текущим пользователем.
        """
        if value and self.request.user.is_authenticated:
            if value is True or str(value).lower() == 'true' or value == '1':
                return queryset.filter(favorites__user=self.request.user)
        return queryset

    def filter_is_in_shopping_cart(self, queryset, name, value):
        """
        Фильтрация по списку покупок.
        Возвращает рецепты, добавленные в корзину текущим пользователем.
        """
        if value and self.request.user.is_authenticated:
            if value is True or str(value).lower() == 'true' or value == '1':
                return queryset.filter(shopping_cart__user=self.request.user)
        return queryset


class IngredientFilter(filters.FilterSet):
    """Фильтр для ингредиентов."""

    name = filters.CharFilter(
        field_name='name',
        lookup_expr='istartswith',
        label='Название (начинается с)'
    )

    class Meta:
        model = Ingredient
        fields = ['name']
