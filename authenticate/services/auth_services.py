from time import daylight

from django.db import transaction
from django.http import JsonResponse

from utils.common import get_clean_request_data
from django.core.exceptions import ValidationError
from services.services import UserService, TransactionLogService
from django.contrib.auth import get_user_model
from authenticate.services.token_service import TokenService
from utils.response_provider import ResponseProvider

from services.otp_email.otp_service import OTPService

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
            max_age=7 * 24 * 60 * 60,
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
    def forgot_password(cls, request):
        """
        for 1 to reset their password they must 1st enter in their personal email
        check if the email exists in the DB and is active if true:
            generate an randoom 6 digit OTP
            sent to their email
            they get the OTP
            enter it into a form field and its verified

        """
        try:
            data = get_clean_request_data(request, required_fields={'email'})

            # verify if email exists
            try:
                user = UserService().get_active_user_by_email(email=data.get('email'))
            except User.DoesNotExist:
                raise ValidationError("No active account found with that email")

            #generate OTP for this user
            OTPService().generate_otp(user=user)

            # send code to user's email — plug in your email service here
            # EmailService.send_otp(user.email, code)

            return ResponseProvider().success(message="OTP sent to your email! Validation 15 minutes")
        except Exception as ex:
            return ResponseProvider().handle_exception(ex)


    @classmethod
    def verify_otp(cls, request):
        try:
            data = get_clean_request_data(request, required_fields={'email', 'otp'})

            try:
                user = UserService().get_active_user_by_email(email=data.get('email'))
            except User.DoesNotExist:
                raise ValidationError("No active account found with that email")

            OTPService().verify_opt(data.get('otp'), user)
            return ResponseProvider().success(message='OTP verified successfully')
        except Exception as ex:
            return ResponseProvider().handle_exception(ex)

    @classmethod
    def reset_password(cls,request):
        try:
            data = get_clean_request_data(request, required_fields={'email', 'new_password'})

            try:
                user = UserService().get_active_user_by_email(email=data.get('email'))
            except User.DoesNotExist:
                raise ValidationError("No active account found with that email")

            user.set_password(data.get('new_password'))
            user.save(update_fields=['password','updated_at'])
            return ResponseProvider().success('password updated successfully')
        except Exception as ex:
            return ResponseProvider().handle_exception(ex)

        