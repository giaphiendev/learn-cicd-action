from django.urls import include, path, re_path
from drf_spectacular.views import SpectacularJSONAPIView, SpectacularRedocView
from drf_yasg import openapi
from drf_yasg.views import get_schema_view
from rest_framework import permissions

from .webhooks import urls as webhook_urls
# from .auth import urls as auth_urls
# from .user import urls as user_urls

app_name = "api"

schema_view = get_schema_view(
    openapi.Info(
        title="Jaseci API",
        default_version='v1',
        description="Welcome to the world of Jaseci",
        terms_of_service="https://www.jaseci.org",
        contact=openapi.Contact(email="jason@jaseci.org"),
        license=openapi.License(name="Awesome IP"),
    ),
    public=True,
    permission_classes=[permissions.AllowAny, ],
)

urlpatterns = (
    [
        # swagger
        path('doc/', schema_view.with_ui('swagger', cache_timeout=0), name='schema-swagger-ui'),  # <-- Here
        re_path('redoc/', schema_view.with_ui('redoc', cache_timeout=0), name='schema-redoc'),  # <-- Here

        # drf_spectacular like swagger
        re_path(r"^schema.json$", SpectacularJSONAPIView.as_view(), name="json_schema"),
        re_path(
            r"^redoc$",
            SpectacularRedocView.as_view(url_name="api:json_schema"),
            name="redoc",
        ),
        # webhook
        path("webhooks/", include(webhook_urls, namespace="webhooks")),
        # path("auth/", include(auth_urls, namespace="auth")),
        # path("user/", include(user_urls, namespace="user")),

    ]
)
