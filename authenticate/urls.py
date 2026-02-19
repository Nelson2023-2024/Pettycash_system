from django.urls import path, include
from authenticate.views import login, logout

urlpatterns = [
  path('login/',login, name='login'),
  path('logout/',logout, name='logout'),
]
