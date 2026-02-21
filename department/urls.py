from django.urls import path
from department import views
from django.http import JsonResponse

urlpatterns = [
    path('', views.get_departments_view, name='get_departments'),
    path('create/', views.create_department_view, name='create_department'),
    path('<str:department_id>/', views.get_department_view, name='get_department'),
    path('<str:department_id>/update/', views.update_department_view, name='update_department'),
    path('<str:department_id>/deactivate/', views.deactivate_department_view, name='deactivate_department'),
]