from rest_framework.pagination import PageNumberPagination
from rest_framework.response import Response

from .constants import PAGE_SIZE


class Pagination(PageNumberPagination):
    """Пагинация для рецептов."""

    page_size_query_param = 'limit'
    page_size = PAGE_SIZE
