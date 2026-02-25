from django.contrib import admin
from django.urls import path, include
from .views import health_check

urlpatterns = [
    path("health/", health_check, name='health'),
    path("auth/", include("authenticate.urls")),
    path("finance/", include("finance.urls")),
    path("department/", include("department.urls")),
]
