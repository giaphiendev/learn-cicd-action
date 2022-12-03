from rest_framework import generics
from rest_framework.settings import api_settings
from rest_framework.views import APIView


class BaseViewWithPagination(generics.GenericAPIView):
    def get_paginated(self, data):
        paginated_data = self.paginate_queryset(data)
        paginated_info = self.get_paginated_response(data)
        return paginated_info, paginated_data


class PaginationApiView(APIView):
    pagination_class = api_settings.DEFAULT_PAGINATION_CLASS

    def get_paginated(self, data):
        paginated_data = self.paginate_queryset(data)
        paginated_info = self.get_paginated_response(data)
        return paginated_info, paginated_data

    @property
    def paginator(self):
        """
        The paginator instance associated with the view, or `None`.
        """
        if not hasattr(self, '_paginator'):
            if self.pagination_class is None:
                self._paginator = None
            else:
                self._paginator = self.pagination_class()
        return self._paginator

    def paginate_queryset(self, queryset):
        """
        Return a single page of results, or `None` if pagination is disabled.
        """
        if self.paginator is None:
            return None
        return self.paginator.paginate_queryset(queryset, self.request, view=self)

    def get_paginated_response(self, data):
        """
        Return a paginated style `Response` object for the given output data.
        """
        if self.paginator is None:
            return None
        return self.paginator.get_paginated_response(data)
