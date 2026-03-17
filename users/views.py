from django.views.decorators.csrf import csrf_exempt
from utils.decorators.login_required import login_required
from utils.decorators.allowed_http_methods import allowed_http_methods
from utils.response_provider import ResponseProvider
from .services.user_services import UserController


# ---------------------------------------------------------------------
# USER — update own profile
# ---------------------------------------------------------------------
@csrf_exempt
@allowed_http_methods("PATCH")
@login_required()
def update_profile_view(request):
    try:
        return UserController.update_profile(request)
    except Exception as ex:
        return ResponseProvider().handle_exception(ex)


# ---------------------------------------------------------------------
# ADMIN — list all users
# ---------------------------------------------------------------------
@csrf_exempt
@allowed_http_methods("GET")
@login_required("ADM")
def list_users_view(request):
    try:
        return UserController.list_users(request)
    except Exception as ex:
        return ResponseProvider().handle_exception(ex)


# ---------------------------------------------------------------------
# ADMIN — get single user
# ---------------------------------------------------------------------
@csrf_exempt
@allowed_http_methods("GET")
@login_required("ADM")
def get_user_view(request, user_id):
    try:
        return UserController.get_user(request, user_id)
    except Exception as ex:
        return ResponseProvider().handle_exception(ex)


# ---------------------------------------------------------------------
# ADMIN — create user
# ---------------------------------------------------------------------
@csrf_exempt
@allowed_http_methods("POST")
@login_required("ADM")
def create_user_view(request):
    try:
        return UserController.create_user(request)
    except Exception as ex:
        return ResponseProvider().handle_exception(ex)


# ---------------------------------------------------------------------
# ADMIN — update user
# ---------------------------------------------------------------------
@csrf_exempt
@allowed_http_methods("PATCH")
@login_required("ADM")
def update_user_view(request, user_id):
    try:
        return UserController.update_user(request, user_id)
    except Exception as ex:
        return ResponseProvider().handle_exception(ex)