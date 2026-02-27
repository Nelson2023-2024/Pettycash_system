import jwt
from functools import wraps

from django.core.exceptions import PermissionDenied

from authenticate.services.token_service import TokenService
from users.models import User
from config.env_config import ENV
from utils.response_provider import ResponseProvider


"""
    Decorator to protect routes with JWT authentication.
    
    Usage:
        @jwt_required()                          # any authenticated user
        @jwt_required(allowed_roles=['FO'])      # Finance Officer only
        @jwt_required(allowed_roles=['FO','CFO']) # Finance Officer or CFO
    """


def login_required(*allowed_roles):
    def decorator(func):
        @wraps(func)
        def wrapper(request, *args, **kwargs):
            auth_header = request.headers.get("Authorization", "")
            if not auth_header.startswith("Bearer "):
                return ResponseProvider.unauthorized(
                    message="Authentication required",
                    error="Authorization header missing or malformed. Expected: Bearer <token>",
                )

            token = auth_header.split(" ")[1]

            if not token:
                return ResponseProvider().unauthorized(
                    message="No bearer token provided"
                )

            try:
                payload = TokenService.decode_access_token(token)
                user = User.objects.select_related("role", "status").get(
                    id=payload["user_id"], is_active=True
                )
                request.user = user

            except PermissionDenied as ex:
                return ResponseProvider.unauthorized(error=str(ex))
            except User.DoesNotExist:
                return ResponseProvider.not_found(error="User not found.")

            # role check
            if allowed_roles and user.role.code not in allowed_roles:
                return ResponseProvider().forbidden(
                    error="You dont have permissions to access this resource"
                )

            return func(request, *args, **kwargs)

        return wrapper

    return decorator
