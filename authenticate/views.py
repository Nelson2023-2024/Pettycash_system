from django.http import JsonResponse
from django.views.decorators.http import require_http_methods
from django.views.decorators.csrf import csrf_exempt

from utils.response_provider import ResponseProvider
from authenticate.services.auth_services import AuthService

# Create your views here.
# @require_http_methods(['POST'])
@csrf_exempt
def login(request) -> JsonResponse:
    try:
        user_data = AuthService.login(request)
        return user_data
    except Exception as ex:
        return ResponseProvider.handle_exception(ex)

def logout(request) -> JsonResponse:
    AuthService.logout(request.user)
    return ResponseProvider.success(message="Logout successful")
