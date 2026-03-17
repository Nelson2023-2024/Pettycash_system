from services.services import RoleService
from utils.response_provider import ResponseProvider


class RoleController:

    @classmethod
    def list_roles(cls, request) -> ResponseProvider:
        """
        Retrieves all active roles.
        Accessible by ADM role only.

        Returns:
            JsonResponse: 200 with list of serialized roles.
        """
        try:
            roles = RoleService().get_all()
            return ResponseProvider.success(
                data=[cls._serialize(role) for role in roles]
            )
        except Exception as ex:
            return ResponseProvider.handle_exception(ex)

    @staticmethod
    def _serialize(role) -> dict:
        return {
            "id": str(role.id),
            "name": role.name,
            "code": role.code,
        }
