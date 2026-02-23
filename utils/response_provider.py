from django.http import JsonResponse
from django.core.serializers.json import DjangoJSONEncoder
from django.core.exceptions import ValidationError, ObjectDoesNotExist, PermissionDenied
from django.db import IntegrityError, OperationalError, DataError
from utils.exceptions import TransactionLogError


class ResponseProvider:
    @staticmethod
    def _response(
        success: bool, code: str, message: str, status: int, data=None, error=None
    ) -> JsonResponse:
        if data is None:
            data = {}

        return JsonResponse(
            data={
                "success": success,
                "code": code,
                "message": message,
                "data": data,
                "error": error or "",
            },
            status=status,
            encoder=DjangoJSONEncoder,
        )

    @classmethod
    def handle_exception(cls, ex: Exception):
        if isinstance(ex, ValidationError):
            if hasattr(ex, "messages"):
                error_message = ", ".join(ex.messages)
            else:
                error_message = str(ex)
            return cls.bad_request(message="Validation Error", error=error_message)
        elif isinstance(ex, ValueError):
            return cls.bad_request(message="Bad Request", error=str(ex))
        elif isinstance(ex, ObjectDoesNotExist):
            return cls.not_found(error=str(ex))
        elif isinstance(ex, PermissionDenied):
            return cls.forbidden(error=str(ex))
        elif isinstance(ex, TypeError):
            return cls.bad_request(message="Invalid data type provided", error=str(ex))
        elif isinstance(ex, ObjectDoesNotExist):
            return cls.not_found(error=str(ex))
        elif isinstance(ex, IntegrityError):
             # e.g. duplicate unique field, FK constraint violation
            return cls.conflict(error="A record with this data already exists or a required relation is missing.")
        elif isinstance(ex, DataError):
            # e.g. value too long for a CharField, out of range for DecimalField
            return cls.bad_request(message="Data error", error="A provided value exceeds the allowed length or range.")
        elif isinstance(ex, OperationalError):
            # e.g. DB connection issues, table doesn't exist
            return cls.service_unavailable(error="A database error occurred. Please try again later.")
        elif isinstance(ex, TransactionLogError):
            return cls.server_error(message='Logging Error', error=str(ex))
        else:
            return cls.server_error(error=str(ex))

    @classmethod
    def success(cls, code="200.00", message="Success", data=None):
        # cls = the class ResponseProvider
        # we use it to call _response from the class
        return cls._response(True, code, message, 200, data=data)

    @classmethod
    def created(cls, code="201.000", message="Created", data=None):
        return cls._response(True, code, message, 201, data=data)

    @classmethod
    def accepted(cls, code="202.000", message="Accepted", data=None):
        return cls._response(True, code, message, 202, data=data)

    @classmethod
    def bad_request(cls, code="400.000", message="Bad Request", error=None):
        return cls._response(False, code, message, 400, error=error)

    @classmethod
    def unauthorized(cls, code="401.000", message="Unauthorized", error=None):
        return cls._response(False, code, message, 401, error=error)

    @classmethod
    def forbidden(cls, code="403.000", message="Forbidden", error=None):
        return cls._response(False, code, message, 403, error=error)

    @classmethod
    def not_found(cls, code="404.000", message="Resource Not Found", error=None):
        return cls._response(False, code, message, 404, error=error)

    @classmethod
    def too_many_requests(
        cls, code="429.000", message="Rate Limit Exceeded", error=None
    ):
        return cls._response(False, code, message, 429, error=error)

    @classmethod
    def server_error(cls, code="500.000", message="Internal Server Error", error=None):
        return cls._response(False, code, message, 500, error=error)

    @classmethod
    def not_implemented(cls, code="501.000", message="Not Implemented", error=None):
        return cls._response(False, code, message, 501, error=error)

    @classmethod
    def service_unavailable(
        cls, code="503.000", message="Service Unavailable", error=None
    ):
        return cls._response(False, code, message, 503, error=error)

    @classmethod
    def conflict(cls, code="409.000", message="Conflict", error=None):

        return cls._response(False, code, message, 409, error=error)
