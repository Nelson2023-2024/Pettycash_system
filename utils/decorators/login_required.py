import jwt
from functools import wraps
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
            token = request.COOKIES.get('jwt')
        
            if not token:
                return ResponseProvider().unauthorized(message='Authentication required')
        
            try:
                payload = jwt.decode(token,ENV.JWT_SECRET,algorithms=['HS256'])
                user = User.objects.select_related('role','status').get(id=payload['user_id'], is_active=True)
                request.user = user
            except jwt.ExpiredSignatureError:
                return ResponseProvider().unauthorized(error='Session expired! please login again')
            except jwt.InvalidTokenError:
                return ResponseProvider().unauthorized(error='Invalid Token')
            except User.DoesNotExist:
                return ResponseProvider().not_found(error='User not found')
        
            # role check
            if  allowed_roles and user.role.code not in allowed_roles:
                return ResponseProvider().unauthorized(error='You dont have permissions to access this resource')
        
            return func(request, *args, **kwargs)
        return wrapper
    return decorator