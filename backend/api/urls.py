from django.urls import include, path

from rest_framework.routers import DefaultRouter

from . import views

app_name = 'api'

router = DefaultRouter()
router.register('users', views.UserViewSet, basename='users')
router.register('recipes', views.RecipeViewSet, basename='recipes')
router.register('ingredients', views.IngredientViewSet, basename='ingredients')
router.register('tags', views.TagViewSet, basename='tags')

urlpatterns = [
    path('', include(router.urls)),

    path('auth/token/login/', views.CustomAuthToken.as_view(), name='login'),
    path('auth/token/logout/', views.LogoutView.as_view(), name='logout'),
]
