from django.core.exceptions import ValidationError
from django.core.validators import MaxValueValidator, MinValueValidator
from django.db import models
from users.models import User

from recipes.constants import (
    AMOUNT_VALIDATION_ERROR,
    COOKING_TIME_VALIDATION_ERROR,
    INGREDIENT_NAME_MAX_LENGTH,
    MAX_AMOUNT,
    MAX_COOKING_TIME,
    MEASUREMENT_UNIT_MAX_LENGTH,
    MIN_AMOUNT,
    MIN_COOKING_TIME,
    RECIPE_NAME_MAX_LENGTH,
    TAG_COLOR_MAX_LENGTH,
    TAG_NAME_MAX_LENGTH,
    TAG_SLUG_MAX_LENGTH,
)


class Ingredient(models.Model):
    """Модель ингредиента."""

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


class Tag(models.Model):
    """Модель тега для категоризации рецептов."""

    name = models.CharField(
        'Название тега',
        max_length=TAG_NAME_MAX_LENGTH,
        unique=True,
        db_index=True,
        help_text='Введите уникальное название тега'
    )
    color = models.CharField(
        'Цвет в HEX',
        max_length=TAG_COLOR_MAX_LENGTH,
        unique=True,
        help_text='Введите цвет в HEX формате (например: #FF0000)'
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

    def clean(self):
        """Валидация цвета в HEX формате."""
        if self.color and not self.color.startswith('#'):
            raise ValidationError(
                'Цвет должен быть в HEX формате (начинаться с #).'
            )
        super().clean()


class Recipe(models.Model):
    """Основная модель рецепта."""

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
        'Картинка рецепта',
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
            MinValueValidator(MIN_COOKING_TIME),
            MaxValueValidator(MAX_COOKING_TIME)
        ],
        help_text=(
            f'Введите время приготовления в минутах '
            f'(от {MIN_COOKING_TIME} до {MAX_COOKING_TIME})'
        )
    )
    pub_date = models.DateTimeField(
        'Дата публикации',
        auto_now_add=True,
        db_index=True
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

    def clean(self):
        """Валидация на уровне модели."""
        if not self.name:
            raise ValidationError('Название рецепта обязательно.')
        if not self.text:
            raise ValidationError('Описание рецепта обязательно.')
        if self.cooking_time:
            if (
                self.cooking_time < MIN_COOKING_TIME
                or self.cooking_time > MAX_COOKING_TIME
            ):
                raise ValidationError({
                    'cooking_time': COOKING_TIME_VALIDATION_ERROR
                })
        super().clean()


class IngredientInRecipe(models.Model):
    """
    Промежуточная модель для связи рецепта и ингредиента.

    Содержит информацию о количестве ингредиента в конкретном рецепте.
    """

    recipe = models.ForeignKey(
        Recipe,
        on_delete=models.CASCADE,
        related_name='ingredient_recipes',
        verbose_name='Рецепт'
    )
    ingredient = models.ForeignKey(
        Ingredient,
        on_delete=models.CASCADE,
        related_name='recipe_ingredients',
        verbose_name='Ингредиент'
    )
    amount = models.PositiveSmallIntegerField(
        'Количество',
        validators=[
            MinValueValidator(MIN_AMOUNT),
            MaxValueValidator(MAX_AMOUNT)
        ],
        help_text=(
            f'Введите количество ингредиента '
            f'(от {MIN_AMOUNT} до {MAX_AMOUNT})'
        )
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
    """Абстрактная базовая модель для связей пользователя с рецептами."""

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
        default_related_name = '%(class)ss'

    def __str__(self):
        return f'{self.user} - {self.recipe}'


class Favorite(BaseUserRecipeRelation):
    """Модель для избранных рецептов пользователя."""

    class Meta(BaseUserRecipeRelation.Meta):
        verbose_name = 'Избранное'
        verbose_name_plural = 'Избранное'
        constraints = [
            models.UniqueConstraint(
                fields=['user', 'recipe'],
                name='unique_favorite'
            )
        ]

    def clean(self):
        """
        Проверка на добавление своего рецепта в избранное.

        Пользователь не может добавить в избранное свой собственный рецепт.
        """
        if self.recipe.author == self.user:
            raise ValidationError('Нельзя добавить свой рецепт в избранное.')
        super().clean()

    def save(self, *args, **kwargs):
        self.full_clean()
        super().save(*args, **kwargs)


class ShoppingCart(BaseUserRecipeRelation):
    """Модель для списка покупок пользователя."""

    class Meta(BaseUserRecipeRelation.Meta):
        verbose_name = 'Список покупок'
        verbose_name_plural = 'Списки покупок'
        constraints = [
            models.UniqueConstraint(
                fields=['user', 'recipe'],
                name='unique_recipe_in_shopping_cart'
            )
        ]

    def save(self, *args, **kwargs):
        self.full_clean()
        super().save(*args, **kwargs)
