from django.conf.locale import tr, en
from django.db import transaction


from utils.common import get_clean_request_data
from django.core.exceptions import ValidationError
from services.services import UserService, TransactionLogService
from django.contrib.auth import get_user_model
from utils.response_provider import ResponseProvider
from services.otp_email.otp_service import OTPService
from ..models import User


class UserController:
    # -------------------------------------------------------------------------
    # USER — Update own profile
    # -------------------------------------------------------------------------
    @classmethod
    def update_profile(cls, request) -> ResponseProvider:
        """

        Authenticated user updates their own profile.
        Allowed fields: phone, avatar, first/last/other name, national_id.
        Role, status, department are NOT user-editable — admin only.
        :param request:
        :return:
        """
        try:
            data = get_clean_request_data(
                request,
                allowed_fields={
                    "first_name",
                    "last_name",
                    "other_name",
                    "phone_number",
                    "national_id",
                    "avatar_url",
                },
            )

            user = request.user  # already resolved by jwt_required decorator

            # capture old values before update
            old_values = {k: str(getattr(user, k, None)) for k in data}
            new_values = {}

            with transaction.atomic():
                for field, value in data.items():
                    setattr(user, field, value)
                    new_values[field] = str(value)
                user.save(update_fields=list(data.keys()) + ["updated_at"])

                TransactionLogService.log(
                    event_code="user_update_profile",
                    triggered_by=user,
                    entity=user,
                    # status_code default ACT
                    message=f"{user.email} updated their profile",
                    ip_address=request.META.get("REMOTE_ADDR"),
                    metadata={
                        "user_id": user.id,
                        "updated_by": user.email,
                        "changed_fields": list(data.keys()),
                        "old_values": old_values,
                        "new_value": new_values,
                    },
                )

            return ResponseProvider.success(
                message="profile updated successfully", data=cls._serialize(user=user)
            )
        except Exception as ex:
            return ResponseProvider.handle_exception(ex)

    # -------------------------------------------------------------------------
    # LIST USERS — admin only
    # -------------------------------------------------------------------------

    @classmethod
    def list_users(cls, request) -> ResponseProvider:
        """
        Returns all users. Admin only (enforced at the decorator level).
        :param request:
        :return:
        """
        try:
            users = UserService.manager.select_related(
                "role", "status", "department"
            ).filter(is_active=True)

            return ResponseProvider.success(
                data=[cls._serialize(user) for user in users]
            )
        except Exception as ex:
            return ResponseProvider.handle_exception(ex)

    # -------------------------------------------------------------------------
    # GET SINGLE USER — admin only
    # -------------------------------------------------------------------------
    @classmethod
    def get_user(cls, request, user_id: User) -> ResponseProvider:
        try:
            user = (
                    UserService.filter(id=user_id, is_active=True)
                    .select_related("role", "department", "status")
                    .first()
                )
            if not user:
                raise ValidationError("User not found.")
            return ResponseProvider.success(data=cls._serialize(user))
        except Exception as ex:
            return ResponseProvider.handle_exception(ex)

    # -------------------------------------------------------------------------
    # CREATE USER — admin only
    # -------------------------------------------------------------------------
    @classmethod
    def create_user(cls, request) -> ResponseProvider:
        """
        Admin creates a new user.
        Required: email, password, first_name, last_name.
        Optional: role, department, phone_number, national_id, status.
        :param request:
        :return:
        """
        try:
            data = get_clean_request_data(
                request,
                required_fields={"email", "password", "first_name", "last_name"},
                allowed_fields={
                    "email",
                    "password",
                    "first_name",
                    "last_name",
                    "other_name",
                    "phone_number",
                    "national_id",
                    "role",
                    "department",
                    "status",
                },
            )
            if UserService.exists(email=data.get("email")):
                raise ValidationError("A user with this email already exists.")

            with transaction.atomic():
                password = data.pop("password")
                user = UserService.manager.create_user(password=password, **data)

                TransactionLogService.log(
                    event_code="user_created",
                    triggered_by=user,
                    entity=user,
                    # status__code ='ACT default,
                    message="User created successfully",
                    metadata={
                        "created_by": request.user.email,
                        "new_user_id": str(user.id),
                        "new_user_email": user.email,
                        "role": user.role.name,
                        "department": user.department.name if user.department else None,
                    },
                )
                return ResponseProvider.success(
                    message="user created successfully", data=cls._serialize(user)
                )
        except Exception as ex:
            return ResponseProvider.handle_exception(ex)

    # -------------------------------------------------------------------------
    # UPDATE USER — admin only (role, department, status, etc.)
    # -------------------------------------------------------------------------
    @classmethod
    def update_user(cls, request, user_id):
        """
        Admin updates any user field including role, department, and status.
        Old and new values are captured and stored in the transaction log.
        Uses transaction.atomic to prevent partial updates if logging fails.
        :param request:
        :param user_id:
        :return:
        """

        try:
            data = get_clean_request_data(
                request,
                allowed_fields={
                    "email",
                    "first_name",
                    "last_name",
                    "other_name",
                    "phone_number",
                    "national_id",
                    "avatar_url",
                    "role",
                    "department",
                    "status",
                    "is_active",
                },
            )

            # Guard — admin cannot deactivate themselves
            if str(request.user.id) == str(user_id) and data.get("is_active") is False:
                raise ValidationError("You cannot deactivate your own account.")

            user = (
                    UserService.filter(id=user_id, is_active=True)
                    .select_related("role", "department", "status")
                    .first()
                )
            if not user:
                    raise ValidationError("User not found.")

            # Normalize is_active from string to bool (checkbox sends "true"/"false")
            if 'is_active' in data:
                raw = str(data['is_active']).strip().lower()
                if raw not in ['true', 'false']:
                    raise ValidationError("is_active must be true or false.")
                data['is_active'] = raw == 'true'

            # old values
            old_values = {k: str(getattr(user, k, None)) for k in data}
            new_values = {}
            with transaction.atomic():
                for field, value in data.items():
                    setattr(user, field, value)
                    new_values[field] = value
                user.save(update_fields=list(data.keys()) + ["updated_at"])

                TransactionLogService.log(
                    event_code="user_updated",
                    triggered_by=request.user,
                    entity=user,
                    status_code="ACT",
                    message=f"Admin {request.user.email} updated user {user.email}",
                    ip_address=request.META.get("REMOTE_ADDR"),
                    metadata={
                        "updated_by": request.user.email,
                        "target_user_id": str(user.id),
                        "target_user_email": user.email,
                        "changed_fields": list(data.keys()),
                        "old_values": old_values,
                        "new_values": new_values,
                    },
                )

            return ResponseProvider.success(
                message="user updated successfully", data=cls._serialize(user)
            )
        except Exception as ex:
            return ResponseProvider.handle_exception(ex)

    @staticmethod
    def _serialize(user: User) -> dict:
        return {
            "email": user.email,
            "first_name": user.first_name,
            "last_name": user.last_name,
            "other_name": user.other_name,
            "phone_number": user.phone_number,
            "national_id": user.national_id,
            "avatar_url": user.avatar_url,
            "last_login": user.last_login,
            "department": user.department.name if user.department else None,
            "is_active": user.is_active,
            "role": user.role.name,
            "status": user.status.name,
        }
