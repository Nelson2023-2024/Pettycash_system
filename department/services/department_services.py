from django.core.exceptions import ValidationError
from utils.response_provider import ResponseProvider
from services.services import DepartmentService, UserService
from utils.common import get_clean_request_data
from department.models import Department
from users.models import User


class DepartmentController:

    @classmethod
    def create_department(cls, request) -> ResponseProvider:
        data = get_clean_request_data(
            request,
            required_fields={
                "name",
                "description",
                "code",
            },
        )
        deparment_name = data.get("name")
        deparment_description = data.get("description")
        deparment_code = data.get("code")

        # get the deppartment by name to check if it already exists
        try:
            department = DepartmentService().get(
                name=deparment_name, code=deparment_code, is_active=True
            )
            raise ValidationError(
                f"Department '{deparment_name}' or {deparment_code} already exists"
            )
        except Department.DoesNotExist:
            pass

        department = DepartmentService().create(
            code=deparment_code,
            name=deparment_name,
            description=deparment_description,
            request=request,
            triggered_by=request.user,
        )

        return ResponseProvider().created(
            message=f"{department.name} created successfully",
            data=cls._serilize(department),
        )

    @classmethod
    def get_departments(cls, request):
        departments = DepartmentService().get_all()
        return ResponseProvider().success(
            data=[cls._serilize(depts) for depts in departments]
        )

    @classmethod
    def get_department(cls, request, department_id):

        try:
            department = DepartmentService().get_by_id(department_id)
            return ResponseProvider().success(data=cls._serilize(department))
        except Department.DoesNotExist:
            return ResponseProvider().not_found(message="Department does not exist")

    @classmethod
    def update_department(cls, request, deparment_id):
        data = get_clean_request_data(
            required_fields={
                "name",
            },
        )
        deparment_id = deparment_id
        department_name = data.get("name")

        department = DepartmentService().update(
            request=request,
            department_id=deparment_id,
            triggered_by=request.user,
            data=data,
        )
        return ResponseProvider().created(
            message=f"{department_name} departement created succesfully",
            data=cls._serilize(department),
        )

    @classmethod
    def deactivate_department(cls, request, deparment_id):

        try:

            department = DepartmentService().deactivate(
                department_id=deparment_id, triggered_by=request.user, request=request
            )
            return ResponseProvider().success(
                message=f"{department.name} department deactivated successfully"
            )

        except Department.DoesNotExist:
            return ResponseProvider().not_found(message="Department does not exist")
        
    
    
    @classmethod
    def assign_line_manager(cls, request, department_id):
        try:
            data = get_clean_request_data(request, required_fields={"manager_id"})

            manager = UserService().get(id=data.get("manager_id"), is_active=True)

            department = DepartmentService().assign_line_manager(
            department_id=department_id,
            manager=manager,
            triggered_by=request.user,
            request=request
        )
            return ResponseProvider().success(
            message=f"Line manager assigned to {department.name} successfully",
            data=cls._serilize(department)
        )
        except User.DoesNotExist:
            return ResponseProvider().not_found(message="Manager not found")
        except Department.DoesNotExist:
            return ResponseProvider().not_found(message="Department not found")


    @staticmethod
    def _serilize(department) -> dict:
        return {
            "id": str(department.id),
            "name": department.name,
            "code": department.code,
            "description": department.description,
        }
