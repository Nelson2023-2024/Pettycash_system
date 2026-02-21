from functools import wraps
from utils.response_provider import ResponseProvider

def allowed_http_methods(*allowed_methods):
    def decorator(func):
        @wraps(func)
        def wrapper(request, *args, **kwargs):
            if allowed_methods and request.method not in allowed_methods:
                return ResponseProvider().bad_request(
                    message='Method not allowed',
                    error=f"{request.method} method is not allowed. Allowed methods: {','.join(allowed_methods)}"       
                )
            return func(request, *args, **kwargs)
        
        return wrapper
    return decorator