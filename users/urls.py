from django.urls import path
from . import views

urlpatterns = [
    # static paths first
    path("", views.list_users_view, name="list_users"),
    path("search/", views.search_users_view, name="search-users"),
    path("create/", views.create_user_view, name="create_user"),
    path("profile/update/", views.update_profile_view, name="update_profile"),
    path("roles/all/", views.list_roles_view, name="list_roles"),

    # dynamic paths last
    path("<str:user_id>/", views.get_user_view, name="get_user"),
    path("<str:user_id>/update/", views.update_user_view, name="update_user"),
]