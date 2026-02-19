from django.http import JsonResponse
from django.views.decorators.http import require_http_methods
from django.views.decorators.csrf import csrf_exempt

from utils.response_provider import ResponseProvider
from authenticate.services.auth_services import AuthService

# Create your views here.
@csrf_exempt
@require_http_methods(['POST'])
def login(request) -> JsonResponse:
    try:
        user_data = AuthService.login(request)
        return user_data
    except Exception as ex:
        return ResponseProvider.handle_exception(ex)

@csrf_exempt
@require_http_methods(['POST'])
def logout(request) -> JsonResponse:
    try:
        return  AuthService.logout()
    except Exception as ex:
        return ResponseProvider.handle_exception(ex)

