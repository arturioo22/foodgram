from django_filters import rest_framework as filters
from recipes.models import Recipe, Ingredient


class RecipeFilter(filters.FilterSet):
    """Фильтр для рецептов."""

    tags = filters.CharFilter(method='filter_tags')
    author = filters.NumberFilter(field_name='author__id')
    is_favorited = filters.BooleanFilter(method='filter_is_favorited')
    is_in_shopping_cart = filters.BooleanFilter(
        method='filter_is_in_shopping_cart'
    )

    class Meta:
        model = Recipe
        fields = ['author', 'tags', 'is_favorited', 'is_in_shopping_cart']

    def filter_tags(self, queryset, name, value):
        """Фильтрация по тегам."""
        if not value:
            return queryset

        tags_values = self.request.query_params.getlist('tags')
        if not tags_values:
            return queryset

        queryset = queryset.filter(tags__slug__in=tags_values).distinct()
        return queryset

    def filter_is_favorited(self, queryset, name, value):
        """Фильтрация по избранному."""
        user = self.request.user
        if value and user.is_authenticated:
            return queryset.filter(favorites__user=user)
        return queryset

    def filter_is_in_shopping_cart(self, queryset, name, value):
        """Фильтрация по списку покупок."""
        user = self.request.user
        if value and user.is_authenticated:
            return queryset.filter(shopping_cart__user=user)
        return queryset


class IngredientFilter(filters.FilterSet):
    """Фильтр для ингредиентов."""

    name = filters.CharFilter(field_name='name', lookup_expr='istartswith')

    class Meta:
        model = Ingredient
        fields = ['name']
