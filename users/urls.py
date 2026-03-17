from django.urls import path
from . import views

urlpatterns = [
    # ADMIN
    path("", views.list_users_view, name="list_users"),
    path("create/", views.create_user_view, name="create_user"),
    path("<str:user_id>/", views.get_user_view, name="get_user"),
    path("<str:user_id>/update/", views.update_user_view, name="update_user"),
    # USER
    path("profile/update/", views.update_profile_view, name="update_profile"),
    # ROLES
    path("roles/all/", views.list_roles_view, name="list_roles"),
]
