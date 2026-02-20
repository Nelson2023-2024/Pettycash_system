from django.db import transaction
from django.http import JsonResponse

from utils.common import get_clean_request_data
from django.core.exceptions import ValidationError
from services.services import UserService, TransactionLogService
from django.contrib.auth import get_user_model
from authenticate.services.token_service import TokenService
from utils.response_provider import ResponseProvider

User = get_user_model()

class AuthService:
    @classmethod
    def login(cls, request) -> JsonResponse:
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

        # Log successful login
        UserService().log_login(user,request)

        user_data = {
            'id': str(user.id),
            'email': user.email,
            'fullname': user.first_name +" "+ user.last_name,
            'status':user.status.name,
            'role':user.role.name,
        }
        response = ResponseProvider.success(message="Login successful", data=user_data)

        # generate token and set cookie
        token = TokenService().generate_token(
            user,
            max_age=30*60,
            response=response,
            cookie_name='jwt'
        )

        return response


    @classmethod
    def logout(cls) -> JsonResponse:
        """
        Logout the current user.
        Delete the cookie
        """
        response = ResponseProvider.success(message='Logout successful')
        response.delete_cookie(key='jwt')
        return response

    @classmethod
    def forgot_password(cls):
        """
        for 1 to reset their password they must 1st enter in their personal email
        check if the email exists in the DB and is active if true:
            generate an randoom 6 digit OTP
            sent to their email
            they get the OTP
            enter it into a form field and its verified

        """
        pass
        