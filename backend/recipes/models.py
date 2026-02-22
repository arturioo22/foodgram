from django.core.exceptions import ValidationError
from django.core.validators import MaxValueValidator, MinValueValidator
from django.db import models

from users.models import User

from .constants import (
    AMOUNT_VALIDATION_ERROR,
    INGREDIENT_NAME_MAX_LENGTH,
    MAX_AMOUNT,
    MAX_COOKING_TIME,
    MEASUREMENT_UNIT_MAX_LENGTH,
    MIN_AMOUNT,
    MIN_COOKING_TIME,
    RECIPE_NAME_MAX_LENGTH,
    TAG_NAME_MAX_LENGTH,
    TAG_SLUG_MAX_LENGTH,
)


class Ingredient(models.Model):
    """
    Модель ингредиента.
    """

    name = models.CharField(
        'Название ингредиента',
        max_length=INGREDIENT_NAME_MAX_LENGTH,
        db_index=True,
        help_text='Введите название ингредиента (например: "Мука", "Сахар")'
    )

    measurement_unit = models.CharField(
        'Единица измерения',
        max_length=MEASUREMENT_UNIT_MAX_LENGTH,
        help_text='Введите единицу измерения (например: "г", "мл", "шт")'
    )

    class Meta:
        verbose_name = 'Ингредиент'
        verbose_name_plural = 'Ингредиенты'
        ordering = ['name']
        constraints = [
            models.UniqueConstraint(
                fields=['name', 'measurement_unit'],
                name='unique_ingredient'
            )
        ]

    def __str__(self):
        return f'{self.name} ({self.measurement_unit})'

    def clean(self):
        """Валидация на уровне модели."""
        if not self.name:
            raise ValidationError('Название ингредиента обязательно.')
        if not self.measurement_unit:
            raise ValidationError('Единица измерения обязательна.')

        super().clean()


class Tag(models.Model):
    """
    Модель тега для категоризации рецептов.
    """

    name = models.CharField(
        'Название тега',
        max_length=TAG_NAME_MAX_LENGTH,
        unique=True,
        db_index=True,
        help_text='Введите уникальное название тега'
    )

    slug = models.SlugField(
        'Уникальный слаг',
        max_length=TAG_SLUG_MAX_LENGTH,
        unique=True,
        db_index=True,
        help_text='Введите уникальный слаг для URL'
    )

    class Meta:
        verbose_name = 'Тег'
        verbose_name_plural = 'Теги'
        ordering = ['name']

    def __str__(self):
        return self.name


class Recipe(models.Model):
    """
    Основная модель рецепта.
    """

    author = models.ForeignKey(
        User,
        on_delete=models.CASCADE,
        related_name='recipes',
        verbose_name='Автор рецепта',
        help_text='Выберите автора рецепта'
    )

    name = models.CharField(
        'Название рецепта',
        max_length=RECIPE_NAME_MAX_LENGTH,
        db_index=True,
        help_text='Введите название рецепта'
    )

    image = models.ImageField(
        'Изображение рецепта',
        upload_to='recipes/',
        help_text='Загрузите изображение рецепта'
    )

    text = models.TextField(
        'Описание рецепта',
        help_text='Опишите процесс приготовления'
    )

    ingredients = models.ManyToManyField(
        Ingredient,
        through='IngredientInRecipe',
        through_fields=('recipe', 'ingredient'),
        verbose_name='Ингредиенты',
        help_text='Выберите ингредиенты для рецепта'
    )

    tags = models.ManyToManyField(
        Tag,
        related_name='recipes',
        verbose_name='Теги',
        help_text='Выберите теги для рецепта'
    )

    cooking_time = models.PositiveSmallIntegerField(
        'Время приготовления (в минутах)',
        validators=[
            MinValueValidator(
                MIN_COOKING_TIME,
                message=(
                    f'Время приготовления должно быть не менее '
                    f'{MIN_COOKING_TIME} минуты.'
                )
            ),
            MaxValueValidator(
                MAX_COOKING_TIME,
                message=(
                    f'Время приготовления не может превышать '
                    f'{MAX_COOKING_TIME} минут (24 часа).'
                )
            )
        ],
        help_text='Введите время приготовления в минутах'
    )

    pub_date = models.DateTimeField(
        'Дата публикации',
        auto_now_add=True,
        db_index=True
    )

    updated = models.DateTimeField(
        'Дата обновления',
        auto_now=True
    )

    class Meta:
        verbose_name = 'Рецепт'
        verbose_name_plural = 'Рецепты'
        ordering = ['-pub_date']
        indexes = [
            models.Index(fields=['name', 'pub_date']),
            models.Index(fields=['author', 'pub_date']),
        ]

    def __str__(self):
        return self.name

    @property
    def favorite_count(self):
        """Количество добавлений в избранное."""
        return self.favorites.count()

    @property
    def shopping_cart_count(self):
        """Количество добавлений в список покупок."""
        return self.shopping_cart.count()


class IngredientInRecipe(models.Model):
    """
    Промежуточная модель для связи
    рецепта и ингредиента с указанием количества.
    """

    recipe = models.ForeignKey(
        Recipe,
        on_delete=models.CASCADE,
        related_name='ingredient_in_recipe',
        verbose_name='Рецепт'
    )

    ingredient = models.ForeignKey(
        Ingredient,
        on_delete=models.CASCADE,
        related_name='ingredient_in_recipe',
        verbose_name='Ингредиент'
    )

    amount = models.PositiveSmallIntegerField(
        'Количество',
        validators=[
            MinValueValidator(
                MIN_AMOUNT,
                message=f'Количество должно быть не менее {MIN_AMOUNT}.'
            ),
            MaxValueValidator(
                MAX_AMOUNT,
                message=f'Количество не может превышать {MAX_AMOUNT}.'
            )
        ],
        help_text='Введите количество ингредиента'
    )

    class Meta:
        verbose_name = 'Ингредиент в рецепте'
        verbose_name_plural = 'Ингредиенты в рецептах'
        ordering = ['ingredient__name']
        constraints = [
            models.UniqueConstraint(
                fields=['recipe', 'ingredient'],
                name='unique_ingredient_in_recipe'
            )
        ]

    def __str__(self):
        return (
            f"{self.ingredient.name} - {self.amount} "
            f"{self.ingredient.measurement_unit}"
        )

    def clean(self):
        """Валидация на уровне модели."""
        if self.amount is None:
            raise ValidationError('Количество не может быть пустым.')

        if self.amount < MIN_AMOUNT or self.amount > MAX_AMOUNT:
            raise ValidationError({
                'amount': AMOUNT_VALIDATION_ERROR
            })

        super().clean()


class BaseUserRecipeRelation(models.Model):
    """
    Абстрактная базовая модель для связей пользователя с рецептами.
    """
    user = models.ForeignKey(
        User,
        on_delete=models.CASCADE,
        verbose_name='Пользователь'
    )

    recipe = models.ForeignKey(
        Recipe,
        on_delete=models.CASCADE,
        verbose_name='Рецепт'
    )

    created = models.DateTimeField(
        'Дата добавления',
        auto_now_add=True
    )

    class Meta:
        abstract = True
        ordering = ['-created']


class Favorite(BaseUserRecipeRelation):
    """
    Модель для избранных рецептов пользователя.
    """
    user = models.ForeignKey(
        User,
        on_delete=models.CASCADE,
        verbose_name='Пользователь',
        related_name='favorites'
    )

    recipe = models.ForeignKey(
        Recipe,
        on_delete=models.CASCADE,
        verbose_name='Рецепт',
        related_name='favorites'
    )

    class Meta(BaseUserRecipeRelation.Meta):
        verbose_name = 'Избранное'
        verbose_name_plural = 'Избранное'
        constraints = [
            models.UniqueConstraint(
                fields=['user', 'recipe'],
                name='unique_favorite'
            )
        ]


class ShoppingCart(BaseUserRecipeRelation):
    """
    Модель для списка покупок пользователя.
    """
    user = models.ForeignKey(
        User,
        on_delete=models.CASCADE,
        verbose_name='Пользователь',
        related_name='shopping_carts'
    )

    recipe = models.ForeignKey(
        Recipe,
        on_delete=models.CASCADE,
        verbose_name='Рецепт',
        related_name='shopping_carts'
    )

    class Meta(BaseUserRecipeRelation.Meta):
        verbose_name = 'Список покупок'
        verbose_name_plural = 'Списки покупок'
        constraints = [
            models.UniqueConstraint(
                fields=['user', 'recipe'],
                name='unique_recipe_in_shopping_cart'
            )
        ]
