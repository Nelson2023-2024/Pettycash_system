import random
from users.models import User
from datetime import datetime, timedelta
from django.utils import timezone

OTP_EXPIRATION_MINUTES = 15


class OTPService:

    @staticmethod
    def generate_otp(user: User):
        """
        Generates a 6 digit OTP, saves it to the user record
        with a 15-minute expiry, and returns the code.

        Args:
            user (User): The user to generate OTP for.

        Returns:
            str: The generated 6 digit OTP code.
        :return:
        """
        try:
            now = timezone.now()

            otp = random.randint(100000, 999999)
            user.otp_code = otp
            user.otp_expires_at = now + timedelta(minutes=OTP_EXPIRATION_MINUTES)
            user.save(update_fields=["otp_code", "otp_expires_at", "updated_at"])

            return otp
        except Exception as ex:
            raise Exception(f"Failed to generate OTP: {str(ex)}")

    @staticmethod
    def verify_opt(otp, user: User):
        """
        Verifies the submitted OTP against the stored one.
        Clears the OTP from the user record after successful verification
        so it cannot be reused.

        Args:
            user (User): The user attempting verification.
            code (str): The OTP code submitted by the user.

        Returns:
            bool: True if valid and not expired.

        Raises:
            ValueError: If OTP is invalid or expired.
        :param otp:
        :param user:
        :return:
        """
        try:

            if not user.otp_code or not user.otp_expires_at:
                raise ValueError("No OTP was requested for this account.")

            # check if length exceed required length
            if len(str(otp)) != 6:
                raise ValueError("OTP must be exactly 6 digits.")

            # check in noow is > the 15 min which after otp had been generated
            if timezone.now() > user.otp_expires_at:
                # set the code and expired_at to Null to prevent reuse
                user.otp_code = None
                user.otp_expires_at = None
                user.save(update_fields=["otp_code", "otp_expires_at"])
                raise ValueError("OTP has expired. Please request a new one.")

            if str(otp) != str(user.otp_code):
                raise ValueError("Invalid OTP code.")

            # set the code and expired_at to Null to prevent reuse
            user.otp_code = None
            user.otp_expires_at = None
            user.save(update_fields=["otp_code", "otp_expires_at"])

            return True

        except ValueError:
            raise
        except Exception as ex:
            raise Exception(f"OTP verification failed: {str(ex)}")
