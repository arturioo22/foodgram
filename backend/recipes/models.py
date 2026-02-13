from django.core.exceptions import ValidationError
from django.core.validators import MaxValueValidator, MinValueValidator
from django.db import models

from users.models import User


class Ingredient(models.Model):
    """
    Модель ингредиента.
    """

    name = models.CharField(
        'Название ингредиента',
        max_length=200,
        db_index=True,
        help_text='Введите название ингредиента (например: "Мука", "Сахар")'
    )

    measurement_unit = models.CharField(
        'Единица измерения',
        max_length=200,
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
        max_length=200,
        unique=True,
        db_index=True,
        help_text='Введите уникальное название тега'
    )

    color = models.CharField(
        'Цвет в HEX',
        max_length=7,
        unique=True,
        help_text='Введите цвет в HEX формате (например: #FF0000)'
    )

    slug = models.SlugField(
        'Уникальный слаг',
        max_length=200,
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
        max_length=200,
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
            MinValueValidator(
                1, message='Время приготовления должно быть не менее 1 минуты.'
            ),
            MaxValueValidator(
                1440, message='Время приготовления не может превышать 24 часа.'
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

    def clean(self):
        """Валидация на уровне модели."""
        if not self.name:
            raise ValidationError('Название рецепта обязательно.')
        if not self.text:
            raise ValidationError('Описание рецепта обязательно.')

        super().clean()

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
        related_name='ingredient_list',
        verbose_name='Рецепт'
    )

    ingredient = models.ForeignKey(
        Ingredient,
        on_delete=models.CASCADE,
        related_name='ingredient_list',
        verbose_name='Ингредиент'
    )

    amount = models.PositiveSmallIntegerField(
        'Количество',
        validators=[
            MinValueValidator(1, message='Количество должно быть не менее 1.'),
            MaxValueValidator(
                10000, message='Количество не может превышать 10000.'
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

        if self.amount <= 0:
            raise ValidationError(
                'Количество должно быть положительным числом.'
            )

        super().clean()


class Favorite(models.Model):
    """
    Модель для избранных рецептов пользователя.
    """

    user = models.ForeignKey(
        User,
        on_delete=models.CASCADE,
        related_name='favorites',
        verbose_name='Пользователь'
    )

    recipe = models.ForeignKey(
        Recipe,
        on_delete=models.CASCADE,
        related_name='favorites',
        verbose_name='Рецепт'
    )

    created = models.DateTimeField(
        'Дата добавления',
        auto_now_add=True
    )

    class Meta:
        verbose_name = 'Избранное'
        verbose_name_plural = 'Избранное'
        ordering = ['-created']
        constraints = [
            models.UniqueConstraint(
                fields=['user', 'recipe'],
                name='unique_favorite'
            )
        ]

    def __str__(self):
        return f'{self.user} - {self.recipe}'

    def clean(self):
        """
        Проверяем, что пользователь не добавляет свой же рецепт в избранное.
        """
        if self.recipe.author == self.user:
            raise ValidationError('Нельзя добавить свой рецепт в избранное.')

        super().clean()

    def save(self, *args, **kwargs):
        """Переопределяем save для вызова full_clean."""
        self.full_clean()
        super().save(*args, **kwargs)


class ShoppingCart(models.Model):
    """
    Модель для списка покупок пользователя.
    """

    user = models.ForeignKey(
        User,
        on_delete=models.CASCADE,
        related_name='shopping_cart',
        verbose_name='Пользователь'
    )

    recipe = models.ForeignKey(
        Recipe,
        on_delete=models.CASCADE,
        related_name='shopping_cart',
        verbose_name='Рецепт'
    )

    created = models.DateTimeField(
        'Дата добавления',
        auto_now_add=True
    )

    class Meta:
        verbose_name = 'Список покупок'
        verbose_name_plural = 'Списки покупок'
        ordering = ['-created']
        constraints = [
            models.UniqueConstraint(
                fields=['user', 'recipe'],
                name='unique_recipe_in_shopping_cart'
            )
        ]

    def __str__(self):
        return f'{self.user} - {self.recipe}'

    def save(self, *args, **kwargs):
        """Переопределяем save для вызова full_clean."""
        self.full_clean()
        super().save(*args, **kwargs)
