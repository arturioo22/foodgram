from django_filters import rest_framework as filters

from recipes.models import Ingredient, Recipe


class RecipeFilter(filters.FilterSet):
    """Фильтр для рецептов."""

    tags = filters.AllValuesMultipleFilter(field_name='tags__slug')
    is_favorited = filters.BooleanFilter(method='filter_is_favorited')
    is_in_shopping_cart = filters.BooleanFilter(
        method='filter_is_in_shopping_cart'
    )

    class Meta:
        model = Recipe
        fields = ['author', 'tags', 'is_favorited', 'is_in_shopping_cart']

    def filter_is_favorited(self, queryset, name, value):
        """
        Фильтрация по избранному.

        Возвращает рецепты, добавленные в избранное текущим пользователем.
        """
        if value and self.request.user.is_authenticated:
            return queryset.filter(favorites__user=self.request.user)
        return queryset

    def filter_is_in_shopping_cart(self, queryset, name, value):
        """
        Фильтрация по списку покупок.

        Возвращает рецепты, добавленные в корзину текущим пользователем.
        """
        if value and self.request.user.is_authenticated:
            return queryset.filter(shopping_carts__user=self.request.user)
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
