from django.urls import re_path

from api.auth.views import (
    CustomRefreshToken,
    LoginView,
    LogoutView,
    CustomSignupPinView,
    CustomSignupView, AdminLoginView,
)

app_name = "api.auth"

urlpatterns = [
    # login and logout view
    re_path(r"login$", LoginView.as_view(), name="custom_login"),
    re_path(r"login-admin$", AdminLoginView.as_view(), name="admin_login"),
    re_path(r"logout$", LogoutView.as_view(), name="custom_logout"),
    # Refresh token
    re_path(r"token/refresh$", CustomRefreshToken.as_view(), name='token_refresh'),
    # Account confirm
    re_path(r"^get-pin$", CustomSignupPinView.as_view(), name="custom_signup_pin"),
    re_path(r"^sign-up$", CustomSignupView.as_view(), name="custom_signup"),
]
