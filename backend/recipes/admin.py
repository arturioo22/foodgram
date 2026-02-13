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
    list_display = ('name', 'author', 'cooking_time', 'pub_date')
    list_filter = ('tags', 'author', 'pub_date')
    search_fields = ('name', 'author__username', 'author__email')
    readonly_fields = ('pub_date', 'updated')
    inlines = [IngredientInRecipeInline]
    filter_horizontal = ('tags',)


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
