from config.env_config import ENV

import jwt
import datetime
from django.utils import timezone
from django.http import JsonResponse
from users.models import User

class TokenService:
    @staticmethod
    def generate_token(user: User, response: JsonResponse, cookie_name,max_age: int) -> str:
        now = timezone.now()
        payload = {
            'user_id': str(user.id),
            'exp':  now + datetime.timedelta(seconds=max_age),
            'iat': now
        }

        token = jwt.encode(payload, ENV.JWT_SECRET, algorithm='HS256' )

        response.set_cookie(
            key=cookie_name,
            value=token,
            max_age=max_age,
            httponly=True, # XSS protection
            samesite='Strict', # CSRF protection
            secure=True #HTTPS only
        )

        return token