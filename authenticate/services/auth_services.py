from django.db import transaction
from django.http import JsonResponse

from services.otp_email.email_service import EmailService
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
        try:
            data = get_clean_request_data(
                request, required_fields={"email", "password"}
            )
            email = data.get("email")
            password = data.get("password")

            try:
                user = UserService().get_active_user_by_email(email)
            except User.DoesNotExist:
                raise ValidationError("Email does not exist")

            if not user.check_password(password):
                raise ValidationError("Invalid password")

            # Delegate persistence
            user = UserService().update_last_login(user)

            # Log successful login
            UserService().log_login(user, request)

            access_token = TokenService.generate_access_token(user=user)
            refresh_token = TokenService.generate_refresh_token(user=user)

            response = ResponseProvider.success(
                message="Login successful",
                data={
                    **cls._serialize(user),
                    "access_token": access_token,
                    "token_type": "Bearer",
                },
            )

            # refresh token in httpOnly cookie — JS cannot read or steal it
            response.set_cookie(
                key="refresh_token",
                value=refresh_token,
                max_age=7 * 24 * 60 * 60,
                httponly=True,
                samesite="Strict",
                secure=False,  # set True in production (HTTPS only)
            )

            return response
        except Exception as ex:
            return ResponseProvider.handle_exception(ex)

    @classmethod
    def refresh(cls, request) -> JsonResponse:
        """
        Silently called by the frontend when the access token expires.
        Reads the refresh token from the httpOnly cookie and
        returns a new access token. User never sees this happening.

        Args:
            request: Must have refresh_token httpOnly cookie.

        Returns:
            JsonResponse: 200 with new access token.
        :param request:
        :return:
        """
        refresh_token = request.COOKIES.get("refresh_token")
        if not refresh_token:
            raise ValidationError("No refresh token found. Please login again.")

        payload = TokenService.decode_refresh_token(token=refresh_token)

        if payload.get("token_type") != "refresh":
            raise ValidationError("Invalid token type")

        try:
            user = User.objects.select_related("role", "status").get(
                id=payload.get("user_id"), is_active=True
            )
        except User.DoesNotExist:
            raise ValidationError("User not Found")

        return ResponseProvider.success(
            data={"access_token": TokenService.generate_access_token(user=user)}
        )

    @classmethod
    def logout(cls, request) -> JsonResponse:
        """
        Logs out the user by clearing the refresh token cookie.
        Frontend is responsible for clearing the access token from memory.

        Args:
            request: The HTTP request object.

        Returns:
            JsonResponse: 200 confirming logout.
        """
        response = ResponseProvider.success(message="Logout successful")
        response.delete_cookie(key="refresh_token")
        return response

    @classmethod
    def get_auth_user(cls, request):
        """
        Returns the currently authenticated user's profile.
        Used on page load to verify session is still valid
        and get fresh user data.

        Args:
            request: The HTTP request object with valid Bearer token.

        Returns:
            JsonResponse: 200 with serialized user data.
        :param request:
        :return:
        """
        return ResponseProvider.success(data=cls._serialize(request.user))

    @classmethod
    def forgot_password(cls, request):
        """
        Step 1 of password reset.
        Verifies email exists and sends a 6 digit OTP valid for 15 minutes.

        Args:
            request: Must contain email in body.

        Returns:
            JsonResponse: 200 confirming OTP was sent.

        """
        try:
            data = get_clean_request_data(request, required_fields={"email"})

            # verify if email exists
            try:
                user = UserService().get_active_user_by_email(email=data.get("email"))
            except User.DoesNotExist:
                raise ValidationError("No active account found with that email")

            # generate OTP for this user
            otp_code = OTPService().generate_otp(user=user)

            # send code to user's email — plug in your email service here
            # EmailService.send_otp(user.email, code)
            EmailService.send_otp(user=user, otp_code=otp_code)

            return ResponseProvider().success(
                message="OTP sent to your email! Validation 15 minutes"
            )
        except Exception as ex:
            return ResponseProvider().handle_exception(ex)

    @classmethod
    def verify_otp(cls, request):
        """
        Step 2 of password reset.
        Verifies the OTP submitted by the user.
        OTP is cleared after successful verification — cannot be reused.

        Args:
            request: Must contain email and otp in body.

        Returns:
            JsonResponse: 200 confirming OTP is valid.
        :param request:
        :return:
        """
        try:
            data = get_clean_request_data(request, required_fields={"email", "otp"})

            try:
                user = UserService().get_active_user_by_email(email=data.get("email"))
            except User.DoesNotExist:
                raise ValidationError("No active account found with that email")

            OTPService().verify_opt(data.get("otp"), user)
            return ResponseProvider().success(message="OTP verified successfully")
        except Exception as ex:
            return ResponseProvider().handle_exception(ex)

    @classmethod
    def reset_password(cls, request):
        """
        Step 3 of password reset.
        Sets the new password after OTP has been verified.

        Args:
            request: Must contain email and new_password in body.

        Returns:
            JsonResponse: 200 confirming password was reset.
        :param request:
        :return:
        """
        try:
            data = get_clean_request_data(
                request, required_fields={"email", "new_password"}
            )

            try:
                user = UserService().get_active_user_by_email(email=data.get("email"))
            except User.DoesNotExist:
                raise ValidationError("No active account found with that email")

            user.set_password(data.get("new_password"))
            user.save(update_fields=["password", "updated_at"])
            return ResponseProvider().success("password updated successfully")
        except Exception as ex:
            return ResponseProvider().handle_exception(ex)

    @staticmethod
    def _serialize(user) -> dict:
        return {
            "id": str(user.id),
            "email": user.email,
            "fullname": user.first_name + " " + user.last_name,
            "status": user.status.name,
            "role": user.role.name,
        }
