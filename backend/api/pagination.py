from rest_framework.pagination import PageNumberPagination


class CustomPagination(PageNumberPagination):
    """Кастомная пагинация."""

    page_size_query_param = 'limit'
    page_size = 6

    def get_paginated_response(self, data):
        from rest_framework.response import Response

        return Response({
            'count': self.page.paginator.count,
            'next': self.get_next_link(),
            'previous': self.get_previous_link(),
            'results': data
        })
