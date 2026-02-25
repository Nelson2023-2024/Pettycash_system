from django.http import JsonResponse
from django.views.decorators.csrf import csrf_exempt
from utils.decorators.allowed_http_methods import allowed_http_methods


@csrf_exempt
@allowed_http_methods("GET")
def health_check(request):
    """
    Simple health check endpoint.
    Returns HTTP 200 with status OK.
    """
    return JsonResponse({"status": "ok"})