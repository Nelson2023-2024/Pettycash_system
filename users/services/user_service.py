from utils.common import get_clean_request_data
from django.core.exceptions import ValidationError
from services.services import UserService
from utils.response_provider import ResponseProvider
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

            user = request.user

            if "avatar_url" in request.FILES:
                data["avatar_url"] = request.FILES["avatar_url"]

            updated_user = UserService().update(
                user_id=user.id,
                data=data,
                triggered_by=user,
                request=request,
            )

            return ResponseProvider.success(
                message="profile updated successfully",
                data=cls._serialize(user=updated_user),
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
                UserService()
                .filter(id=user_id, is_active=True)
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
                },
            )
            if UserService().exists(email=data.get("email")):
                raise ValidationError("A user with this email already exists.")

            password = data.pop("password")
            data = cls._resolve_foreign_key(data)
            user = UserService().create(
                password=password,
                triggered_by=request.user,
                request=request,
                **data,
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

            # Normalize is_active from string to bool (checkbox sends "true"/"false")
            if "is_active" in data:
                raw = str(data["is_active"]).strip().lower()
                if raw not in ["true", "false"]:
                    raise ValidationError("is_active must be true or false.")
                data["is_active"] = raw == "true"

            data = cls._resolve_foreign_key(data)

            user = UserService().update(
                user_id=user_id,
                data=data,
                triggered_by=request.user,
                request=request,
            )

            return ResponseProvider.success(
                message="user updated successfully", data=cls._serialize(user)
            )
        except Exception as ex:
            return ResponseProvider.handle_exception(ex)

    @classmethod
    def _resolve_foreign_key(cls, data: dict) -> dict:
        """Resolves UUID strings to model instances for ForeignKey fields bcoz create_user required model instances."""
        from department.models import Department
        from users.models import Role

        if "department" in data and data["department"]:
            try:
                data["department"] = Department.objects.get(id=data["department"])
            except Department.DoesNotExist:
                raise ValueError("Department not found.")

        if "role" in data and data["role"]:
            try:
                data["role"] = Role.objects.get(code=data["role"])
            except Role.DoesNotExist:
                raise ValueError("Role not found.")

        return data

    @staticmethod
    def _serialize(user: User) -> dict:
        return {
            "id": user.id,
            "email": user.email,
            "first_name": user.first_name,
            "last_name": user.last_name,
            "other_name": user.other_name,
            "phone_number": user.phone_number,
            "national_id": user.national_id,
            "avatar_url": user.avatar_url.url if user.avatar_url else None,
            "last_login": user.last_login,
            "department": (
                {
                    "id": str(user.department.id),
                    "name": user.department.name,
                }
                if user.department
                else None
            ),
            "is_active": user.is_active,
            "role": user.role.name,
            "role_code": user.role.code,
            "status": user.status.name,
        }
