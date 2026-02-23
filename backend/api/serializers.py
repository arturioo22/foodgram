from rest_framework import serializers

from djoser.serializers import UserSerializer as DjoserUserSerializer
from drf_extra_fields.fields import Base64ImageField

from api.constants import (
    ERROR_MESSAGES,
    MAX_AMOUNT,
    MAX_COOKING_TIME,
    MIN_AMOUNT,
    MIN_COOKING_TIME,
)
from recipes.models import Ingredient, IngredientInRecipe, Recipe, Tag
from users.models import User


class UserSerializer(DjoserUserSerializer):
    """Сериализатор для пользователя."""

    is_subscribed = serializers.SerializerMethodField()
    avatar = serializers.SerializerMethodField()

    class Meta(DjoserUserSerializer.Meta):
        model = User
        fields = (
            'email', 'id', 'username', 'first_name',
            'last_name', 'is_subscribed', 'avatar'
        )

    def get_is_subscribed(self, obj):
        request = self.context.get('request')
        return (request and request.user.is_authenticated
                and request.user.follower.filter(author=obj).exists())

    def get_avatar(self, obj):
        """Получить URL аватара пользователя."""
        if obj.avatar:
            request = self.context.get('request')
            if request:
                return request.build_absolute_uri(obj.avatar.url)
            return obj.avatar.url
        return None


class AvatarSerializer(serializers.ModelSerializer):
    """Сериализатор для обновления аватара."""

    avatar = Base64ImageField(required=True, allow_null=False)

    class Meta:
        model = User
        fields = ('avatar',)

    def update(self, instance, validated_data):
        if instance.avatar:
            instance.avatar.delete(save=False)
        instance.avatar = validated_data.get('avatar')
        instance.save()
        return instance


class IngredientSerializer(serializers.ModelSerializer):
    """Сериализатор для ингредиентов."""

    class Meta:
        model = Ingredient
        fields = ('id', 'name', 'measurement_unit')


class TagSerializer(serializers.ModelSerializer):
    """Сериализатор для тегов."""

    class Meta:
        model = Tag
        fields = ('id', 'name', 'slug')


class IngredientInRecipeWriteSerializer(serializers.ModelSerializer):
    """Сериализатор для записи ингредиентов в рецепте."""

    id = serializers.PrimaryKeyRelatedField(
        queryset=Ingredient.objects.all(),
        source='ingredient'
    )
    amount = serializers.IntegerField(
        min_value=MIN_AMOUNT,
        max_value=MAX_AMOUNT,
        error_messages={
            'min_value': ERROR_MESSAGES['min_amount'],
            'max_value': ERROR_MESSAGES['max_amount'],
            'required': ERROR_MESSAGES['required'],
            'blank': ERROR_MESSAGES['blank'],
        }
    )

    class Meta:
        model = IngredientInRecipe
        fields = ('id', 'amount')


class IngredientInRecipeReadSerializer(serializers.ModelSerializer):
    """Сериализатор для чтения ингредиентов в рецепте."""

    id = serializers.ReadOnlyField(source='ingredient.id')
    name = serializers.ReadOnlyField(source='ingredient.name')
    measurement_unit = serializers.ReadOnlyField(
        source='ingredient.measurement_unit'
    )
    amount = serializers.IntegerField(read_only=True)

    class Meta:
        model = IngredientInRecipe
        fields = ('id', 'name', 'measurement_unit', 'amount')


class ShortRecipeSerializer(serializers.ModelSerializer):
    """Сериализатор для краткого отображения рецепта."""

    class Meta:
        model = Recipe
        fields = ('id', 'name', 'image', 'cooking_time')


class RecipeReadSerializer(serializers.ModelSerializer):
    """Сериализатор для чтения рецептов."""

    author = UserSerializer(read_only=True)
    tags = TagSerializer(many=True, read_only=True)
    ingredients = IngredientInRecipeReadSerializer(
        many=True,
        source='ingredient_in_recipe',
        read_only=True
    )
    is_favorited = serializers.SerializerMethodField()
    is_in_shopping_cart = serializers.SerializerMethodField()

    class Meta:
        model = Recipe
        fields = (
            'id', 'tags', 'author', 'ingredients',
            'is_favorited', 'is_in_shopping_cart',
            'name', 'image', 'text', 'cooking_time'
        )

    def _check_relation(self, obj, relation_manager):
        """Общий метод для проверки наличия объекта в списке пользователя."""
        request = self.context.get('request')
        return (
            request
            and request.user.is_authenticated
            and relation_manager.filter(user=request.user).exists()
        )

    def get_is_favorited(self, obj):
        """Проверяет, находится ли рецепт в избранном у пользователя."""
        return self._check_relation(obj, obj.favorites)

    def get_is_in_shopping_cart(self, obj):
        """Проверяет, находится ли рецепт в корзине у пользователя."""
        return self._check_relation(obj, obj.shopping_carts)


class RecipeWriteSerializer(serializers.ModelSerializer):
    """Сериализатор для создания и обновления рецептов."""

    ingredients = IngredientInRecipeWriteSerializer(many=True, required=True)
    tags = serializers.PrimaryKeyRelatedField(
        queryset=Tag.objects.all(),
        many=True,
        required=True
    )
    image = Base64ImageField(required=True)
    cooking_time = serializers.IntegerField(
        min_value=MIN_COOKING_TIME,
        max_value=MAX_COOKING_TIME,
        required=True,
        error_messages={
            'min_value': ERROR_MESSAGES['min_time'],
            'max_value': ERROR_MESSAGES['max_time'],
            'required': ERROR_MESSAGES['required'],
            'blank': ERROR_MESSAGES['blank'],
        }
    )

    class Meta:
        model = Recipe
        fields = (
            'ingredients', 'tags', 'image',
            'name', 'text', 'cooking_time'
        )
        read_only_fields = ('author',)

    def validate(self, data):
        """
        Общая валидация данных рецепта.

        Проверяет наличие ингредиентов и тегов, отсутствие дубликатов.
        """
        ingredients = data.get('ingredients')
        tags = data.get('tags')

        if not ingredients:
            raise serializers.ValidationError({
                'ingredients': ERROR_MESSAGES['at_least_one_ingredient']
            })

        if not tags:
            raise serializers.ValidationError({
                'tags': ERROR_MESSAGES['at_least_one_tag']
            })

        ingredient_ids = [item['ingredient'].id for item in ingredients]
        if len(ingredient_ids) != len(set(ingredient_ids)):
            raise serializers.ValidationError({
                'ingredients': ERROR_MESSAGES['duplicate_ingredients']
            })

        if len(tags) != len(set(tags)):
            raise serializers.ValidationError({
                'tags': ERROR_MESSAGES['duplicate_tags']
            })

        return data

    def validate_image(self, value):
        """Валидация поля image."""
        if not value:
            raise serializers.ValidationError(ERROR_MESSAGES['required'])
        return value

    def _create_ingredients(self, recipe, ingredients_data):
        """Общий метод для создания ингредиентов рецепта."""
        ingredient_objs = [
            IngredientInRecipe(
                recipe=recipe,
                ingredient=item['ingredient'],
                amount=item['amount']
            )
            for item in ingredients_data
        ]
        IngredientInRecipe.objects.bulk_create(ingredient_objs)

    def create(self, validated_data):
        """Создание нового рецепта."""
        ingredients_data = validated_data.pop('ingredients')
        tags_data = validated_data.pop('tags')

        request = self.context.get('request')
        validated_data['author'] = request.user

        recipe = Recipe.objects.create(**validated_data)
        recipe.tags.set(tags_data)
        self._create_ingredients(recipe, ingredients_data)
        return recipe

    def update(self, instance, validated_data):
        """Обновление существующего рецепта."""
        ingredients_data = validated_data.pop('ingredients')
        tags_data = validated_data.pop('tags')

        instance.tags.set(tags_data)
        instance.ingredient_in_recipe.all().delete()
        self._create_ingredients(instance, ingredients_data)

        return super().update(instance, validated_data)

    def to_representation(self, instance):
        """Возвращает данные в формате RecipeReadSerializer."""
        return RecipeReadSerializer(
            instance,
            context=self.context
        ).data


class SubscriptionSerializer(UserSerializer):
    """Сериализатор для подписок с рецептами."""

    recipes = serializers.SerializerMethodField()
    recipes_count = serializers.IntegerField(
        source='recipes.count',
        read_only=True
    )

    class Meta(UserSerializer.Meta):
        fields = UserSerializer.Meta.fields + (
            'recipes', 'recipes_count'
        )

    def get_recipes(self, obj):
        request = self.context.get('request')
        recipes = obj.recipes.all()

        if request and 'recipes_limit' in request.query_params:
            try:
                limit = int(request.query_params.get('recipes_limit'))
                if limit > 0:
                    recipes = recipes[:limit]
            except (ValueError, TypeError):
                pass

        return ShortRecipeSerializer(
            recipes,
            many=True,
            context={'request': request}
        ).data
