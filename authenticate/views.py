from django.http import JsonResponse
from django.views.decorators.http import require_http_methods
from django.views.decorators.csrf import csrf_exempt

from utils.decorators.login_required import login_required
from utils.response_provider import ResponseProvider
from authenticate.services.auth_services import AuthService


# Create your views here.
@csrf_exempt
@require_http_methods(["POST"])
def login(request) -> JsonResponse:
    try:
        user_data = AuthService.login(request)
        return user_data
    except Exception as ex:
        return ResponseProvider.handle_exception(ex)


@csrf_exempt
@require_http_methods(["POST"])
def refresh_token(request) -> JsonResponse:

    return AuthService.refresh(request)


@csrf_exempt
@require_http_methods(["POST"])
def logout(request) -> JsonResponse:
    try:
        return AuthService.logout()
    except Exception as ex:
        return ResponseProvider.handle_exception(ex)


@csrf_exempt
@require_http_methods(["GET"])
@login_required()
def get_auth_user(request) -> JsonResponse:
    return AuthService.get_auth_user(request)


@csrf_exempt
@require_http_methods(["POST"])
def forgot_password(request):
    return AuthService().forgot_password(request)


@csrf_exempt
@require_http_methods(["POST"])
def verify_otp(request):
    return AuthService().verify_otp(request)


@csrf_exempt
@require_http_methods(["POST"])
def reset_password(request):
    return AuthService().reset_password(request)
