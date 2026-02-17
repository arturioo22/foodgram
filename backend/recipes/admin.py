from django.contrib import admin

from .models import (
    Favorite,
    Ingredient,
    IngredientInRecipe,
    Recipe,
    ShoppingCart,
    Tag
)


class IngredientInRecipeInline(admin.TabularInline):
    """Инлайн для отображения ингредиентов в рецепте."""

    model = IngredientInRecipe
    extra = 1
    min_num = 1


@admin.register(Ingredient)
class IngredientAdmin(admin.ModelAdmin):
    """Админка для ингредиентов."""

    list_display = ('name', 'measurement_unit')
    list_filter = ('measurement_unit',)
    search_fields = ('name',)
    ordering = ('name',)


@admin.register(Tag)
class TagAdmin(admin.ModelAdmin):
    """Админка для тегов."""

    list_display = ('name', 'color', 'slug')
    search_fields = ('name', 'slug')
    prepopulated_fields = {'slug': ('name',)}


@admin.register(Recipe)
class RecipeAdmin(admin.ModelAdmin):
    """Админка для рецептов."""

    list_display = (
        'name',
        'author',
        'cooking_time',
        'pub_date',
        'get_tags',
        'get_ingredients',
        'favorite_count'
    )
    list_filter = ('tags', 'author', 'pub_date')
    search_fields = ('name', 'author__username', 'author__email')
    readonly_fields = ('pub_date',)
    inlines = [IngredientInRecipeInline]
    filter_horizontal = ('tags',)

    @admin.display(description='Теги')
    def get_tags(self, obj):
        """
        Получение списка тегов рецепта.

        Возвращает строку с названиями тегов, разделёнными запятыми.
        """
        return ", ".join([tag.name for tag in obj.tags.all()])

    @admin.display(description='Ингредиенты')
    def get_ingredients(self, obj):
        """
        Получение списка ингредиентов рецепта.

        Возвращает строку с названиями ингредиентов, разделёнными запятыми.
        """
        ingredients = obj.ingredient_list.select_related('ingredient')
        return ", ".join([
            f"{item.ingredient.name} "
            f"({item.amount} {item.ingredient.measurement_unit})"
            for item in ingredients
        ])

    @admin.display(description='В избранном')
    def favorite_count(self, obj):
        """
        Получение количества добавлений рецепта в избранное.

        Возвращает число, сколько раз рецепт был добавлен в избранное.
        """
        return obj.favorited_by.count()


@admin.register(Favorite)
class FavoriteAdmin(admin.ModelAdmin):
    """Админка для избранного."""

    list_display = ('user', 'recipe', 'created')
    list_filter = ('created',)
    search_fields = ('user__username', 'recipe__name')


@admin.register(ShoppingCart)
class ShoppingCartAdmin(admin.ModelAdmin):
    """Админка для списка покупок."""

    list_display = ('user', 'recipe', 'created')
    list_filter = ('created',)
    search_fields = ('user__username', 'recipe__name')
