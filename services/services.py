from django.db import transaction
from django.db.models import Manager
from typing import Type

from finance.models import (
    PettyCashAccount,
    ExpenseRequest,
    TopUpRequest,
    DisbursementReconciliation,
)
from base.models import Status, Category
from department.models import Department
from audit.models import EventTypes, TransactionLogBase, Notifications
from users.models import User, Role
from services.serviceBase import ServiceBase
from django.utils import timezone


class StatusService(ServiceBase):
    manager = Status.objects


class CategoryService(ServiceBase):
    manager = Category.objects


class RoleService(ServiceBase):
    manager = Role.objects


class UserService(ServiceBase):
    manager = User.objects

    ## AUTHENTICATION QUERIES

    """
    LOGIN usage
    This method retrieves an active user from the database based on the provided email address u. 
    It returns the user object if found; otherwise, it raises a `DoesNotExist` exception if no active user matches the email.
    """

    def get_active_user_by_email(self, email):
        return self.manager.get(email=email, is_active=True)

    @staticmethod
    def update_last_login(user: User) -> User:
        from django.utils import timezone

        user.last_login = timezone.now()
        user.save(update_fields=["last_login"])
        return user

    @staticmethod
    def log_login(user: User, request) -> None:
        TransactionLogService().log(
            event_code="user_login_success",
            triggered_by=user,
            entity=user,
            status_code="ACT",
            message=f"{user.email} logged in successfully",
            ip_address=request.META.get("REMOTE_ADDR"),
            metadata={
                "user_id": str(user.id),
                "email": user.email,
                "role": user.role.name,
                "department": user.department.name if user.department else None,
                "user_agent": request.META.get("HTTP_USER_AGENT"),
                "device_type": (
                    "mobile"
                    if "Mobile" in request.META.get("HTTP_USER_AGENT", "")
                    else "desktop"
                ),
                "ip_address": request.META.get("REMOTE_ADDR"),
                "forwarded_ip": request.META.get("HTTP_X_FORWARDED_FOR"),
                "login_method": "email_password",
                "login_at": timezone.now().isoformat(),
            },
        )


# -----------------------------------------------------------------------------
# DEPARMENT SERVICE
# -----------------------------------------------------------------------------
class DepartmentService(ServiceBase):
    manager = Department.objects

    def create(
        self,
        name: str,
        description: str,
        code: str,
        line_manager=None,
        triggered_by: str = None,
        request=None,
    ):
        department = self.manager.create(
            name=name, description=description, code=code, line_manager=line_manager
        )

        TransactionLogService().log(
            entity=department,
            event_code="department_created",
            triggered_by=triggered_by,
            ip_address=request.META.get("REMOTE_ADDR") if request else None,
            message=f"{name} department created successfully",
            metadata={
                "department_id": str(department.id),
                "department_name": department.name,
                "department_code": department.code,
                "description": department.description,
                "line_manager_id": str(line_manager.id) if line_manager else None,
                "line_manager_name": (
                    line_manager.get_full_name() if line_manager else None
                ),
                "created_by_id": str(triggered_by.id) if triggered_by else None,
                "created_by_email": triggered_by.email if triggered_by else None,
                "created_by_role": triggered_by.role.name if triggered_by else None,
                "request_ip": request.META.get("REMOTE_ADDR") if request else None,
                "user_agent": request.META.get("HTTP_USER_AGENT") if request else None,
                "created_at": timezone.now().isoformat(),
            },
        )

        return department

    def get_all(self):
        departments = self.manager.filter(is_active=True).select_related("line_manager")
        return departments

    def get_by_id(self, department_id: str):
        department = self.manager.get(id=department_id, is_active=True)
        return department

    def get_by_code(self, code: str):
        deparment = self.manager.get(code=code, is_active=True)

        return deparment

    def update(self, department_id: str, data: dict, triggered_by: User, request=None):
        department = self.get_by_id(department_id)

        # capture old values
        old_values = {}
        for field in data.keys():
            old_values[field] = str(getattr(department, field, None))

        new_values = {}
        # new values
        for field, value in data.items():
            setattr(department, field, value)
            new_values[field] = getattr(department, field)

        department.save(update_fields=list(data.keys()))

        # Log update
        metadata = {
            "department_id": str(department.id),
            "department_name": department.name,
            "updated_fields": list(data.keys()),
            "old_values": old_values,
            "new_values": new_values,
            "updated_by_id": str(triggered_by.id),
            "updated_by_email": triggered_by.email,
            "updated_by_role": triggered_by.role.name,
            "request_ip": request.META.get("REMOTE_ADDR") if request else None,
            "user_agent": request.META.get("HTTP_USER_AGENT") if request else None,
            "action": "update",
            "updated_at": timezone.now().isoformat(),
        }

        TransactionLogService().log(
            entity=department,
            event_code="department_updated",
            triggered_by=triggered_by,
            ip_address=request.META.get("REMOTE_ADDR") if request else None,
            message=f"{department.name} department updated",
            metadata=metadata,
        )

        return department

    def deactivate(self, department_id: str, triggered_by: User, request=None):
        department = self.get_by_id(department_id)
        department.is_active = False
        department.save(update_fields=["is_active"])

        # Log deactivation
        metadata = {
            "department_id": str(department.id),
            "department_name": department.name,
            "deactivated_by_id": str(triggered_by.id),
            "deactivated_by_email": triggered_by.email,
            "deactivated_by_role": triggered_by.role.name,
            "request_ip": request.META.get("REMOTE_ADDR") if request else None,
            "user_agent": request.META.get("HTTP_USER_AGENT") if request else None,
            "action": "deactivate",
            "deactivated_at": timezone.now().isoformat(),
        }

        TransactionLogService().log(
            entity=department,
            event_code="department_deactivated",
            triggered_by=triggered_by,
            ip_address=request.META.get("REMOTE_ADDR") if request else None,
            message=f"{department.name} department deactivated",
            metadata=metadata,
        )

        return department


class EventTypeService(ServiceBase):
    manager = EventTypes.objects

    def get_by_category(self, category_code):
        return self.manager.filter(event_category__code=category_code)

    def get_active(self):
        return self.manager.filter(is_active=True)


# -----------------------------------------------------------------------------
# TRANSACTION LOG SERVICE
# -----------------------------------------------------------------------------
class TransactionLogService(ServiceBase):
    manager = TransactionLogBase.objects

    @staticmethod
    def log(
        event_code: str,
        triggered_by: User,
        entity,
        status_code: str = "ACT",
        message: str = "",
        metadata: dict = None,
        ip_address: str = None,
    ) -> TransactionLogBase:
        event_type = EventTypes.objects.get(code=event_code)
        status = Status.objects.get(code=status_code)

        return TransactionLogBase.objects.create(
            event_type=event_type,
            triggered_by=triggered_by,
            status=status,
            event_message=message,
            metadata=metadata or {},
            entity_type=entity.__class__.__name__,  # "User", "ExpenseRequest" etc
            entity_id=str(entity.pk),
            user_ip_address=ip_address,
        )

    @staticmethod
    def get_logs_for_entity(entity):
        """get all logs for a specific entity e.g. user, expense"""
        return TransactionLogBase.objects.filter(
            entity_type=entity.__class__.__name__, entity_id=str(entity.pk)
        ).select_related("event_type", "triggered_by", "status")

    @staticmethod
    def get_logs_by_event(event_code: str):
        """Get all logs for a specific event e.g all logins"""
        return TransactionLogBase.objects.filter(
            event_type__code=event_code
        ).select_related("event_type", "triggered_by", "status")

    @staticmethod
    def get_user_logs(user: User):
        """Everything a specific user has triggered"""
        return TransactionLogBase.objects.filter(triggered_by=user).select_related(
            "event_type", "status"
        )


class NotificationService(ServiceBase):
    manager = Notifications.objects

    def get_unread(self, user_id):
        return self.manager.filter(recipient__id=user_id, is_read=False)

    def get_by_recipient(self, user_id):
        return self.manager.filter(recipient__id=user_id)

    def mark_as_read(self, uuid):
        return self.filter(id=uuid).update(is_read=True)


# -----------------------------------------------------------------------------
# PETTY CASH ACCOUNT SERVICE
# -----------------------------------------------------------------------------
class PettyCashAccountService(ServiceBase):
    manager = PettyCashAccount.objects

    def create_account(
        self,
        name,
        description,
        mpesa_phone_number,
        minimum_threshold,
        triggered_by: User,
        request=None,
    ):
        account = self.manager.create(
            name=name,
            description=description,
            mpesa_phone_number=mpesa_phone_number,
            minimum_threshold=minimum_threshold,
        )

        try:
            TransactionLogService().log(
                entity=account,
                event_code="petty_cash_account_created",
                ip_address=request.META.get("REMOTE_ADDR") if request else None,
                triggered_by=triggered_by,
                message=f'Petty cash account "{account.name}" created',
                metadata={
                    "account_id": str(account.id),
                    "account_name": account.name,
                    "minimum_threshold": str(minimum_threshold),
                    "mpesa_phone_number": mpesa_phone_number,
                    "created_by": triggered_by.email,
                },
            )
        except Exception as e:
            print(f"[TransactionLog ERROR] {e}")  # you'll see the real reason now

        return account

    def get_by_id(self, account_id: str):
        return self.manager.get(id=account_id, is_active=True)

    def update_account(self, account_id: str, data: dict, triggered_by, request=None):
        account = self.get_by_id(account_id)

        # Capture old values before update for audit trail
        old_values = {}
        for field, value in data.items():
            # getattr(account, "name") returns "Original Name"
            old_values[field] = str(getattr(account, field, None))

        for field, value in data.items():
            setattr(account, field, value)

        account.save(update_fields=list(data.keys()))

        TransactionLogService.log(
            event_code="petty_cash_account_updated",
            triggered_by=triggered_by,
            entity=account,
            status_code="ACT",
            message=f'Petty cash account "{account.name}" updated',
            ip_address=request.META.get("REMOTE_ADDR") if request else None,
            metadata={
                "account_id": str(account.id),
                "account_name": account.name,
                "updated_by": triggered_by.email,
                "changed_fields": list(data.keys()),
                "old_values": old_values,  # what it was before
                "new_values": {
                    k: str(v) for k, v in data.items()
                },  # what it changed to
            },
        )
        return account

    def deactivate_account(self, account_id: str, triggered_by, request=None):
        account = self.manager.get(id=account_id)
        account.is_active = False
        account.save(update_fields=["is_active"])

        TransactionLogService().log(
            entity=account,
            ip_address=request.META.get("REMOTE_ADDR") if request else None,
            message=f"Petty cash account {account.name} deactivated",
            triggered_by=triggered_by,
            status_code="INACT",
            event_code="petty_cash_account_updated",
            metadata={
                "account_id": str(account.id),
                "account_name": account.name,
                "deactivated_by": triggered_by.email,
                "action": "deactivate",
            },
        )
        return account


class ExpenseRequestService(ServiceBase):
    manager = ExpenseRequest.objects

    def create(
        self,
        request,
        title: str,
        mpesa_phone: str,
        description: str,
        amount: float,
        employee: User,
        assigned_to: User,
        category: Category,
        expense_type: str,
        receipt_url: list = None,
    ):
        """
        Creates a new expense request for the given employee.
        Category, status, and assigned_to are auto-resolved via defaults in the models.
        """
        expense = self.manager.create(
            employee=employee,
            expense_type=expense_type,
            assigned_to=assigned_to,
            title=title,
            mpesa_phone=mpesa_phone,
            description=description,
            amount=amount,
            receipt_url=receipt_url or [],
        )
        TransactionLogService.log(
            entity=expense,
            event_code="expense_created",
            triggered_by=employee,
            message=f'Expense request "{expense.title}" created',
            ip_address=request.META.get("REMOTE_ADDR") if request else None,
            metadata={
                "expense_id": str(expense.id),
                "title": expense.title,
                "amount": str(expense.amount),
                "expense_type": expense.expense_type,
                "mpesa_phone": expense.mpesa_phone,
                "description": expense.description,
                "employee_id": str(employee.id),
                "employee_email": employee.email,
                "assigned_to_id": str(assigned_to.id) if assigned_to else None,
                "assigned_to_email": assigned_to.email if assigned_to else None,
                "receipt_url": receipt_url or [],
                "action": "create",
            },
        )

        return expense

    def get_all(self):
        """
        Retrieves all expense requests with their related employee, assigned user,
        and status pre-fetched in a single optimized query via select_related.

        Returns:
            QuerySet: A queryset of all ExpenseRequest instances ordered by created_at (desc),
            with employee, assigned_to, and status fields already joined —
            avoiding N+1 queries when serializing.
        """
        return self.manager.select_related("employee", "assigned_to", "status").all()

    def get_my_expense_requests(
        self,
        authUser,
    ):
        """
        Retrieves all expense requests belonging to the authenticated employee.

        Args:
            auth_user (User): The currently authenticated user making the request.

        Returns:
            QuerySet: ExpenseRequest instances where employee matches auth_user,
            with assigned_to and status pre-fetched via select_related.
        """
        return self.manager.filter(employee=authUser).select_related(
            "status", "assigned_to"
        )

    def update(self, expense_id: str, data: dict, triggered_by: User, request=None):
        """
        Updates an expense request with the provided fields.
        Uses select_for_update to prevent race conditions on concurrent updates.

        Args:
            expense_id (str): The ID of the expense request to update.
            data (dict): Dictionary of fields to update and their new values.
                triggered_by (User): The user performing the update.
        request: Optional HTTP request for logging IP and user agent.

        Returns:
            ExpenseRequest: The updated expense request instance.

        Raises:
            ExpenseRequest.DoesNotExist: If no matching expense request is found.
        """
        with transaction.atomic():
            expense = (
                self.manager.select_for_update()
                .select_related("status")
                .get(id=expense_id)
            )

        old_values = {}

        for field in data.keys():
            old_values[field] = str(getattr(expense, field, None))

        new_values = {}
        for field, value in data.items():
            setattr(expense, field, value)
            new_values[field] = getattr(expense, field)

        TransactionLogService.log(
            entity=expense,
            event_code="expense_updated",
            triggered_by=triggered_by,
            message=f'Expense request "{expense.title}" updated',
            ip_address=request.META.get("REMOTE_ADDR") if request else None,
            metadata={
                "expense_id": str(expense.id),
                "title": expense.title,
                "updated_fields": list(data.keys()),
                "old_values": old_values,
                "new_values": new_values,
                "updated_by_id": str(triggered_by.id),
                "updated_by_email": triggered_by.email,
                "updated_by_role": triggered_by.role.name,
                "employee_id": str(expense.employee.id),
                "employee_email": expense.employee.email,
                "action": "update",
            },
        )

        expense.save(update_fields=list(data.keys()) + ["updated_at"])

    def deactivate(self, request, expense_request_id, triggered_by: User):
        """
        Deactivates an expense request by setting its status to inactive and is_active -> False.

        Args:
            expense_request_id (UUID): The ID of the expense request to deactivate.

        Returns:
            ExpenseRequest: The updated expense request instance.

        Raises:
            ExpenseRequest.DoesNotExist: If no matching expense request is found.
        """
        expense = self.manager.select_related("status").get(id=expense_request_id)
        inactive_status, _ = Status.objects.get_or_create(
            code="INACT",
            defaults={"name": "Inactive", "description": "Deactivated record"},
        )

        expense.status = inactive_status
        expense.is_active = False
        expense.save(update_fields=["is_active", "status"])

        TransactionLogService.log(
            entity=expense,
            event_code="expense_updated",
            triggered_by=triggered_by,
            status_code="INACT",
            message=f'Expense request "{expense.title}" deactivated',
            ip_address=request.META.get("REMOTE_ADDR") if request else None,
            metadata={
                "expense_id": str(expense.id),
                "title": expense.title,
                "amount": str(expense.amount),
                "expense_type": expense.expense_type,
                "employee_id": str(expense.employee.id),
                "employee_email": expense.employee.email,
                "deactivated_by_id": str(triggered_by.id),
                "deactivated_by_email": triggered_by.email,
                "deactivated_by_role": triggered_by.role.name,
                "action": "deactivate",
            },
        )

        return expense


class TopUpRequestService(ServiceBase):
    manager = TopUpRequest.objects

    def get_by_status(self, status_code):
        return self.manager.filter(status__code=status_code)

    def get_by_requester(self, user_id):
        return self.manager.filter(requested_by__id=user_id)

    def get_auto_triggered(self):
        return self.manager.filter(is_auto_triggered=True)


class DisbursementReconciliationService(ServiceBase):
    manager = DisbursementReconciliation.objects

    def get_by_status(self, status_code):
        return self.manager.filter(status__code=status_code)

    def get_by_submitter(self, user_id):
        return self.manager.filter(submitted_by__id=user_id)

    def get_by_expense_request(self, expense_request_id):
        return self.manager.filter(expense_request__id=expense_request_id).first()
