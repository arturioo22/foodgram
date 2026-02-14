import base64
import uuid

from django.contrib.auth import authenticate
from django.core.files.base import ContentFile
from django.utils.translation import gettext_lazy as _

from rest_framework import serializers

from recipes.models import (
    Favorite, Ingredient, IngredientInRecipe, Recipe, ShoppingCart, Tag
)
from users.models import Follow, User


class Base64ImageField(serializers.ImageField):
    """Кастомное поле для обработки base64 изображений."""

    def to_internal_value(self, data):
        if isinstance(data, str) and data.startswith('data:image'):
            format, imgstr = data.split(';base64,')
            ext = format.split('/')[-1]
            data = ContentFile(
                base64.b64decode(imgstr),
                name=f'{uuid.uuid4()}.{ext}'
            )
        return super().to_internal_value(data)


class CustomTokenCreateSerializer(serializers.Serializer):
    """Сериализатор для создания токена с email."""

    email = serializers.EmailField(
        label=_("Email"),
        write_only=True
    )
    password = serializers.CharField(
        label=_("Password"),
        style={'input_type': 'password'},
        trim_whitespace=False,
        write_only=True
    )

    def validate(self, attrs):
        email = attrs.get('email')
        password = attrs.get('password')

        if email and password:
            user = authenticate(
                request=self.context.get('request'),
                username=email,
                password=password
            )

            if not user:
                msg = _('Неверный email или пароль.')
                raise serializers.ValidationError(msg, code='authorization')
        else:
            msg = _('Должны быть указаны "email" и "password".')
            raise serializers.ValidationError(msg, code='authorization')

        attrs['user'] = user
        return attrs


class CustomUserCreateSerializer(serializers.ModelSerializer):
    """Сериализатор для создания пользователя."""

    class Meta:
        model = User
        fields = (
            'email', 'id', 'username', 'first_name', 'last_name', 'password'
        )
        extra_kwargs = {
            'password': {'write_only': True},
            'email': {'required': True},
            'username': {'required': True},
            'first_name': {'required': True},
            'last_name': {'required': True}
        }

    def create(self, validated_data):
        user = User.objects.create_user(
            email=validated_data['email'],
            username=validated_data['username'],
            first_name=validated_data['first_name'],
            last_name=validated_data['last_name'],
            password=validated_data['password']
        )
        return user


class CustomUserSerializer(serializers.ModelSerializer):
    """Сериализатор для пользователя."""

    is_subscribed = serializers.SerializerMethodField()
    avatar = Base64ImageField(required=False, allow_null=True)

    class Meta:
        model = User
        fields = (
            'email', 'id', 'username', 'first_name',
            'last_name', 'is_subscribed', 'avatar'
        )
        read_only_fields = ('id', 'is_subscribed')

    def get_is_subscribed(self, obj):
        request = self.context.get('request')
        if request and request.user.is_authenticated:
            return Follow.objects.filter(
                user=request.user, author=obj
            ).exists()
        return False


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
    amount = serializers.IntegerField(min_value=1)

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

    author = CustomUserSerializer(read_only=True)
    tags = TagSerializer(many=True, read_only=True)
    ingredients = IngredientInRecipeReadSerializer(
        many=True,
        source='ingredient_list',
        read_only=True
    )
    is_favorited = serializers.SerializerMethodField()
    is_in_shopping_cart = serializers.SerializerMethodField()
    image = serializers.SerializerMethodField()

    class Meta:
        model = Recipe
        fields = (
            'id', 'tags', 'author', 'ingredients',
            'is_favorited', 'is_in_shopping_cart',
            'name', 'image', 'text', 'cooking_time'
        )

    def get_image(self, obj):
        """Всегда возвращаем строку URL или пустую строку."""
        if obj.image:
            request = self.context.get('request')
            if request:
                return request.build_absolute_uri(obj.image.url)
            return obj.image.url
        return ""

    def get_is_favorited(self, obj):
        request = self.context.get('request')
        if request and request.user.is_authenticated:
            return Favorite.objects.filter(
                user=request.user, recipe=obj
            ).exists()
        return False

    def get_is_in_shopping_cart(self, obj):
        request = self.context.get('request')
        if request and request.user.is_authenticated:
            return ShoppingCart.objects.filter(
                user=request.user, recipe=obj
            ).exists()
        return False


class RecipeWriteSerializer(serializers.ModelSerializer):
    """Сериализатор для создания и обновления рецептов."""

    ingredients = IngredientInRecipeWriteSerializer(many=True, required=True)
    tags = serializers.PrimaryKeyRelatedField(
        queryset=Tag.objects.all(),
        many=True,
        required=True
    )
    image = Base64ImageField(required=True)
    name = serializers.CharField(required=True, max_length=200)
    text = serializers.CharField(required=True)
    cooking_time = serializers.IntegerField(required=True, min_value=1)

    class Meta:
        model = Recipe
        fields = (
            'ingredients', 'tags', 'image',
            'name', 'text', 'cooking_time'
        )
        read_only_fields = ('author',)

    def validate_ingredients(self, value):
        if not value:
            raise serializers.ValidationError(
                'Добавьте хотя бы один ингредиент.'
            )

        ingredient_ids = [item['ingredient'].id for item in value]
        if len(ingredient_ids) != len(set(ingredient_ids)):
            raise serializers.ValidationError(
                'Ингредиенты не должны повторяться.'
            )

        for item in value:
            if item['amount'] < 1:
                raise serializers.ValidationError(
                    "Количество ингредиентов должно быть не менее 1."
                )

        return value

    def validate_tags(self, value):
        if not value:
            raise serializers.ValidationError(
                'Добавьте хотя бы один тег.'
            )
        tag_ids = [tag.id for tag in value]
        if len(tag_ids) != len(set(tag_ids)):
            raise serializers.ValidationError(
                'Теги не должны повторяться.'
            )
        return value

    def validate_name(self, value):
        if not value or not value.strip():
            raise serializers.ValidationError(
                'Название рецепта не может быть пустым.'
            )
        return value

    def validate_text(self, value):
        if not value or not value.strip():
            raise serializers.ValidationError(
                'Описание рецепта не может быть пустым.'
            )
        return value

    def validate_cooking_time(self, value):
        if value is None:
            raise serializers.ValidationError(
                'Время приготовления обязательно.'
            )
        if value < 1:
            raise serializers.ValidationError(
                'Время приготовления должно быть не менее 1 минуты.'
            )
        return value

    def validate(self, data):
        """Кастомная валидация для разных методов."""
        request = self.context.get('request')

        if not request:
            return data

        if request.method == 'POST':
            required_fields = [
                'ingredients', 'tags', 'image', 'name', 'text', 'cooking_time']
            for field in required_fields:
                if field not in data:
                    raise serializers.ValidationError({
                        field: 'Это поле обязательно.'
                    })
                if field in ['ingredients', 'tags'] and not data[field]:
                    raise serializers.ValidationError({
                        field: f'Добавьте хотя бы один {field}.'
                    })

        elif request.method == 'PATCH':
            if 'ingredients' in data and not data['ingredients']:
                raise serializers.ValidationError({
                    'ingredients': 'Добавьте хотя бы один ингредиент.'
                })

            if 'tags' in data and not data['tags']:
                raise serializers.ValidationError({
                    'tags': 'Добавьте хотя бы один тег.'
                })

            if 'image' in data and not data['image']:
                raise serializers.ValidationError({
                    'image': 'Это поле не может быть пустым.'
                })

            if 'name' in data and (
                not data['name'] or not data['name'].strip()
            ):
                raise serializers.ValidationError({
                    'name': 'Название рецепта не может быть пустым.'
                })

            if 'text' in data and (
                not data['text'] or not data['text'].strip()
            ):
                raise serializers.ValidationError({
                    'text': 'Описание рецепта не может быть пустым.'
                })

            if 'cooking_time' in data and data['cooking_time'] is None:
                raise serializers.ValidationError({
                    'cooking_time': 'Время приготовления обязательно.'
                })

        return data

    def create(self, validated_data):
        ingredients_data = validated_data.pop('ingredients')
        tags_data = validated_data.pop('tags')

        request = self.context.get('request')
        validated_data['author'] = request.user

        recipe = Recipe.objects.create(**validated_data)
        recipe.tags.set(tags_data)

        ingredient_objs = []
        for ingredient_data in ingredients_data:
            ingredient_objs.append(
                IngredientInRecipe(
                    recipe=recipe,
                    ingredient=ingredient_data['ingredient'],
                    amount=ingredient_data['amount']
                )
            )
        IngredientInRecipe.objects.bulk_create(ingredient_objs)

        return recipe

    def update(self, instance, validated_data):
        ingredients_data = validated_data.pop('ingredients', None)
        tags_data = validated_data.pop('tags', None)

        request = self.context.get('request')

        if request and request.method == 'PATCH':
            if 'ingredients' not in self.initial_data:
                raise serializers.ValidationError({
                    'ingredients': 'Добавьте хотя бы один ингредиент.'
                })
            if ingredients_data is not None and len(ingredients_data) == 0:
                raise serializers.ValidationError({
                    'ingredients': 'Добавьте хотя бы один ингредиент.'
                })
            if 'tags' not in self.initial_data:
                raise serializers.ValidationError({
                    'tags': 'Добавьте хотя бы один тег.'
                })
            if tags_data is not None and len(tags_data) == 0:
                raise serializers.ValidationError({
                    'tags': 'Добавьте хотя бы один тег.'
                })

        for attr, value in validated_data.items():
            setattr(instance, attr, value)
        instance.save()

        if tags_data is not None:
            instance.tags.set(tags_data)

        if ingredients_data is not None:
            instance.ingredient_list.all().delete()

            ingredient_objs = []
            for ingredient_data in ingredients_data:
                ingredient_objs.append(
                    IngredientInRecipe(
                        recipe=instance,
                        ingredient=ingredient_data['ingredient'],
                        amount=ingredient_data['amount']
                    )
                )
            IngredientInRecipe.objects.bulk_create(ingredient_objs)

        return instance

    def to_representation(self, instance):
        """Возвращает данные в формате RecipeReadSerializer."""
        return RecipeReadSerializer(
            instance,
            context=self.context
        ).data


class SubscriptionSerializer(CustomUserSerializer):
    """Сериализатор для подписок с рецептами."""

    recipes = serializers.SerializerMethodField()
    recipes_count = serializers.IntegerField(
        source='recipes.count',
        read_only=True
    )

    class Meta(CustomUserSerializer.Meta):
        fields = CustomUserSerializer.Meta.fields + ('recipes', 'recipes_count')

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
