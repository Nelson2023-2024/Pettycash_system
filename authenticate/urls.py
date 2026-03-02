from django.urls import path, include
from authenticate.views import (
    forgot_password,
    get_auth_user,
    login,
    logout,
    refresh_token,
    reset_password,
    verify_otp,
)

urlpatterns = [
    path("login/", login, name="login"),
    path("logout/", logout, name="logout"),
    path("refresh/", refresh_token, name="refresh-token"),
    path("me/", get_auth_user, name="get-auth-user"),
    path("forgot-password/", forgot_password, name="forgot-password"),
    path("verify-otp/", verify_otp, name="verify-otp"),
    path("reset-password/", reset_password, name="reset-password"),
]
