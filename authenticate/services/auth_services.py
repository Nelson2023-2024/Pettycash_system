from django.db import transaction
from utils.common import get_clean_request_data
from django.core.exceptions import ValidationError
from services.services import UserService
from django.contrib.auth import get_user_model
from django.utils import timezone
import datetime
import jwt

User = get_user_model()

class AuthService:
    @classmethod
    def login(cls, request) -> dict:
        """
        Authenticate a user with email and password.
        update the last_login to now()
        Returns a dict with token and basic user info on success.
        Raises ValidationError on failure.
        """
        data = get_clean_request_data(request,required_fields={'email', 'password'})
        email = data.get('email')
        password = data.get('password')

        try:
            user = UserService().get_active_user_by_email(email)
        except User.DoesNotExist:
            raise ValidationError('Email does not exist')

        if not user.check_password(password):
            raise ValidationError('Invalid password')

        # Delegate persistence
        user = UserService().update_last_login(user)

        # authenticate the user accessToken - 15 minutes refreshToken - 7 days
        now = timezone.now()

        payload = {
            "user_id": str(user.id),
            "email": user.email,
            "role": user.role.code,
            "exp": now + datetime.timedelta(minutes=30),
            "iat": now,
        }

        access_token = jwt.encode(payload, 'ssefre', algorithm="HS256")

        return {
            'id': str(user.id),
            'email': user.email,
            'fullname': user.first_name +" "+ user.last_name,
            'status':user.status.name,
            'role':user.role.name,
            'token': access_token
        }

    @classmethod
    def logout(cls, user) -> None:
        """
        Logout the current user.
        Extend this if you have tokens/sessions to invalidate.
        """
        pass