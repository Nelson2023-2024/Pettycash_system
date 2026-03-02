from config.env_config import ENV

import jwt
import datetime
from django.utils import timezone
from django.http import JsonResponse
from users.models import User

from django.core.exceptions import PermissionDenied


class TokenService:
    @staticmethod
    def _generate_token(
        user: User, secret: str, expiry: datetime.timedelta, token_type: str
    ) -> str:
        """
        Base token generator — reused by access and refresh token methods.

        Args:
            user (User): The user to generate token for.
            secret (str): The secret key to sign the token.
            expiry (timedelta): How long the token is valid for.
            token_type (str): 'access' or 'refresh'.

        Returns:
            str: Signed JWT token.
        :param user:
        :param secret:
        :param expiry:
        :param token_type:
        :return:
        """
        now = timezone.now()
        payload = {
            "user_id": str(user.id),
            "token_type": token_type,
            "iat": now,
            "exp": now + expiry,
        }

        return jwt.encode(payload, secret, algorithm="HS256")

    @staticmethod
    def _decode_token(token: str, secret: str) -> dict:
        """
        Base token decoder — reused by access and refresh decode methods.

        Args:
            token (str): The JWT token to decode.
            secret (str): The secret key used to sign the token.

        Returns:
            dict: Decoded payload.

        Raises:
            PermissionDenied: If token is expired or invalid.
        :param token:
        :return:
        """
        try:
            return jwt.decode(token, secret, algorithms=["HS256"])
        except jwt.ExpiredSignatureError:
            raise PermissionDenied("Token has expired.")
        except jwt.InvalidTokenError:
            raise PermissionDenied("Invalid token.")
        except Exception as ex:
            raise PermissionDenied(
                f"An error occurred while decoding the token: {str(ex)}"
            )

    @classmethod
    def generate_access_token(cls, user: User) -> str:
        """
        Generates a short-lived access token — 15 minutes.
        Sent in Authorization header for every API request.
        :param user:
        :return:
        """
        return cls._generate_token(
            user=user,
            secret=ENV.JWT_ACCESS_SECRET,
            token_type="access",
            expiry=datetime.timedelta(minutes=15),
        )

    @classmethod
    def generate_refresh_token(cls, user: User):
        """
        Generates a long-lived refresh token — 7 days.
        Used only to silently obtain a new access token when it expires.
        Stored in httpOnly cookie on web, SecureStorage on mobile.
        :param user:
        :return:
        """

        return cls._generate_token(
            token_type="refresh",
            secret=ENV.JWT_REFRESH_SECRET,
            user=user,
            expiry=datetime.timedelta(days=7),
        )

    @classmethod
    def decode_access_token(cls, token):
        """
        Decodes and validates an access token.
        :param token:
        :return:
        """
        return cls._decode_token(token, secret=ENV.JWT_ACCESS_SECRET)

    @classmethod
    def decode_refresh_token(cls, token):
        """
        Decodes and validates a refresh token.
        :param token:
        :return:
        """
        return cls._decode_token(token, secret=ENV.JWT_REFRESH_SECRET)
