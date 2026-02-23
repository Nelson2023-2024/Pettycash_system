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
from utils.exceptions import TransactionLogError


class StatusService(ServiceBase):
    manager = Status.objects


class CategoryService(ServiceBase):
    manager = Category.objects


class RoleService(ServiceBase):
    manager = Role.objects


# -----------------------------------------------------------------------------
# USER SERVICE
# -----------------------------------------------------------------------------
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
        try:
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
        except Exception as e:
            raise TransactionLogError(f"Failed to create transaction log for event '{event_code}': {str(e)}")

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
        """
                Creates a new petty cash account.
        Guards against creating more than one active account if org policy requires it.

        Args:
            name (str): Name of the petty cash account.
            description (str): Description of the account.
            mpesa_phone_number (str): M-Pesa phone number for disbursements.
            minimum_threshold (Decimal): The balance threshold that triggers an auto top-up.
            triggered_by (User): The user creating the account.
            request: Optional HTTP request for logging IP and user agent.

        Returns:
            PettyCashAccount: The newly created petty cash account instance.

        Raises:
            ValueError: If an active petty cash account already exists.

        """

        existing = self.manager.filter(is_active=True).exists()
        if existing:
            raise ValueError(
                "An active petty cash account already exists. Deactivate it before creating a new one."
            )
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
        """
        Retrieves a single active petty cash account by ID.

        Args:
            account_id (str): The UUID of the petty cash account.

        Returns:
            PettyCashAccount: The matching active account instance.

        Raises:
            PettyCashAccount.DoesNotExist: If no active account matches the given ID.
        """
        return self.manager.get(id=account_id, is_active=True)

    def get_active_accounts(self):
        """
        Retrieves all active petty cash accounts.

        Returns:
            QuerySet: PettyCashAccount instances where is_active is True.
        """
        return self.manager.filter(is_active=True)

    def get_all(self):
        """
        Retrieves all petty cash accounts including inactive ones.

        Returns:
            QuerySet: All PettyCashAccount instances.

        """
        return self.manager.all()

    def update_account(self, account_id: str, data: dict, triggered_by, request=None):
        """
            Updates a petty cash account with the provided fields.

        Args:
            account_id (str): The UUID of the petty cash account to update.
            data (dict): Dictionary of fields to update and their new values.
            triggered_by (User): The user performing the update.
            request: Optional HTTP request for logging IP and user agent.

        Returns:
            PettyCashAccount: The updated petty cash account instance.

        Raises:
            PettyCashAccount.DoesNotExist: If no active account matches the given ID.

        """
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
        """
            Soft deletes a petty cash account by setting is_active to False.
        Uses the base manager to bypass the is_active filter so already
        inactive accounts can still be found if needed.

        Args:
            account_id (str): The UUID of the petty cash account to deactivate.
            triggered_by (User): The user performing the deactivation.
            request: Optional HTTP request for logging IP and user agent.

        Returns:
            PettyCashAccount: The updated petty cash account instance.

        Raises:
            PettyCashAccount.DoesNotExist: If no account matches the given ID.

        """
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



# -----------------------------------------------------------------------------
# EXPENSE REQUEST SERVICE
# -----------------------------------------------------------------------------
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
        return self.manager.filter(is_active=True).select_related("employee", "assigned_to", "status")

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
        return self.manager.filter(employee=authUser, is_active=True).select_related(
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
            
            expense.save(update_fields=list(data.keys()) + ["updated_at"])

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

        
        
        return expense

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


# -----------------------------------------------------------------------------
# TOPUP REQUEST SERVICE
# -----------------------------------------------------------------------------
class TopUpRequestService(ServiceBase):
    manager = TopUpRequest.objects

    def get_by_id(self, topup_id: str):
        """Retrieves a single top-up request by ID."""
        return self.manager.select_related(
            "pettycash_account", "requested_by", "decision_by", "status"
        ).get(id=topup_id, is_active=True)

    def get_all(self):
        """Retrieves all active top-up requests with related fields pre-fetched."""
        return self.manager.select_related(
            "pettycash_account", "requested_by", "decision_by", "status"
        ).filter(is_active=True)

    def get_by_account(self, account_id: str):
        """Retrieves all active top-up requests for a specific petty cash account."""
        return self.manager.select_related(
            "requested_by", "decision_by", "status", "event_type"
        ).filter(pettycash_account__id=account_id, is_active=True)

    def get_by_status(self, status_code: str):
        """Retrieves all top-up requests matching a given status code."""
        return self.manager.select_related(
            "pettycash_account", "requested_by", "status", "event_type"
        ).filter(status__code=status_code, is_active=True)

    def get_authuser_top_up_requests(self, auth_user: User):
        """Retrieves all top-up requests made by the authenticated user."""
        return self.manager.select_related(
            "pettycash_account", "status", "event_type"
        ).filter(requested_by=auth_user, is_active=True)

    def create_top_up_request(
        self,
        request,
        pettycash_account_id,
        requested_by: User,
        request_reason: str,
        amount: float,
    ):
        """
        Creates a new top-up request for a petty cash account.

        Args:
            pettycash_account_id (str): The ID of the petty cash account to top up.
            requested_by (User): The user requesting the top-up.
            reason (str): Reason for the top-up request.
            amount (float): The amount to top up.
            request: Optional HTTP request for logging IP and user agent.

        Returns:
            TopUpRequest: The newly created top-up request instance.
        """
        # retrieve the petty cash account
        account = PettyCashAccountService().get_by_id(pettycash_account_id)

        topup = self.manager.create(
            pettycash_account=account,
            amount=amount,
            requested_by=requested_by,
            request_reason=request_reason,
            # status auto-resolves to 'pending' via model default
            # event_type auto-resolves to 'topup_requested' via model default
        )

        TransactionLogService.log(
            entity=topup,
            event_code="topup_requested",
            triggered_by=requested_by,
            message=f'Top-up request of {amount} created for account "{account.name}"',
            ip_address=request.META.get("REMOTE_ADDR") if request else None,
            metadata={
                "topup_id": str(topup.id),
                "account_id": str(account.id),
                "account_name": account.name,
                "amount": str(amount),
                "request_reason": request_reason,
                "status": topup.status.name if topup.status else None,
                "event_type": topup.event_type.code if topup.event_type else None,
                "requested_by_id": str(requested_by.id),
                "requested_by_email": requested_by.email,
                "requested_by_role": requested_by.role.name,
                "is_auto_triggered": topup.is_auto_triggered,
                "action": "create",
            },
        )

        return topup

    def trigger_top_up_request(
        self, account: PettyCashAccount, request=None
    ) -> TopUpRequest:
        """
        Auto-triggers a top-up request when a petty cash account balance
        drops below its minimum threshold. No user interaction required.

        Called automatically after any balance deduction — not exposed as an API endpoint.

        Args:
            account (PettyCashAccount): The petty cash account to check.

        Returns:
            TopUpRequest: The newly created top-up request if triggered.
            None: If balance is still above threshold or a pending request already exists.

        """
        # guard 1 — balance still above threshold, no action needed
        if account.current_balance >= account.minimum_threshold:
            return None

        # guard 2 — a pending top-up already exists for this account, don't create a duplicate
        already_pending = TopUpRequest.objects.filter(
            pettycash_account=account, status__code="pending", is_active=True
        ).exists()

        if already_pending:
            raise ValueError(
                f"[AutoTopUp] Skipped — pending top-up already exists for '{account.name}'"
            )

        # auto-resolve the system user to act as requested_by
        system_user = User.objects.filter(role__code="SYS").first()

        if not system_user:
            raise ValueError(
                f"[AutoTopUp ERROR] No system user found — cannot auto-trigger top-up for '{account.name}'"
            )

        # calculate top-up amount to bring balance back above threshold
        top_up_amount = account.minimum_threshold - account.current_balance

        topup = self.manager.create(
            pettycash_account=account,
            requested_by=system_user,
            request_reason=f"Auto-triggered: balance ({account.current_balance}) dropped below minimum threshold ({account.minimum_threshold})",
            amount=top_up_amount,
            is_auto_triggered=True,  # flag so you can distinguish in admin/reports
            # status auto-resolves to 'pending' via model default
            # event_type auto-resolves to 'topup_requested' via model default
        )

        TransactionLogService.log(
            entity=topup,
            event_code="topup_requested",
            triggered_by=system_user,
            message=f'Auto top-up of {top_up_amount} triggered for "{account.name}" — balance below threshold',
            metadata={
                "topup_id": str(topup.id),
                "account_id": str(account.id),
                "account_name": account.name,
                "current_balance": str(account.current_balance),
                "minimum_threshold": str(account.minimum_threshold),
                "top_up_amount": str(top_up_amount),
                "is_auto_triggered": True,
                "action": "auto_trigger",
            },
        )

        return topup

    def decide_top_up_request(
        self,
        request,
        topup_id: str,
        decision: str,
        triggered_by: User,
        decision_reason: str,
    ):
        """
        Approves or rejects a top-up request in a single method.

        Args:
            topup_id (str): The ID of the top-up request.
            decision (str): Either 'approved' or 'rejected'.
            triggered_by (User): The user making the decision.
            reason (str, optional): Required when rejecting, optional for approval.
            request: Optional HTTP request for logging IP and user agent.

        Returns:
            TopUpRequest: The updated top-up request instance.

        Raises:
            ValueError: If decision is not 'approved' or 'rejected'.
            TopUpRequest.DoesNotExist: If no matching top-up request is found.
        """
        topup = self.get_by_id(topup_id)
        status = Status.objects.get(code=decision)
        event_code = "topup_approved" if decision == "approved" else "topup_rejected"
        event_type = EventTypes.objects.get(code=event_code)
        decision_at = timezone.now()

        topup.status = status
        topup.event_type = event_type
        topup.decision_by = triggered_by
        topup.decision_reason = decision_reason
        topup.metadata = {**topup.metadata, "decision_at": decision_at.isoformat()}
        topup.save(
            update_fields=[
                "status_id",
                "event_type_id",
                "decision_by_id",
                "decision_reason",
                "metadata",
                "updated_at",
            ]
        )

        TransactionLogService.log(
            entity=topup,
            event_code=event_code,
            triggered_by=triggered_by,
            message=f'Top-up of {topup.amount} {decision} for "{topup.pettycash_account.name}"',
            ip_address=request.META.get("REMOTE_ADDR") if request else None,
            metadata={
                "topup_id": str(topup.id),
                "account_id": str(topup.pettycash_account.id),
                "account_name": topup.pettycash_account.name,
                "amount": str(topup.amount),
                "decision": decision,
                "decision_reason": decision_reason,
                "decision_at": decision_at.isoformat(),
                "request_reason": topup.request_reason,
                "decided_by_id": str(triggered_by.id),
                "decided_by_email": triggered_by.email,
                "decided_by_role": triggered_by.role.name,
                "action": decision,
            },
        )

        return topup

    def update_topup_request(
        self, topup_id: str, data: dict, triggered_by: User, request=None
    ):
        """
            Updates a top-up request with the provided fields.
        Uses select_for_update to prevent race conditions on concurrent updates.

        Args:
            topup_id (str): The ID of the top-up request to update.
            data (dict): Dictionary of fields to update and their new values.
            triggered_by (User): The user performing the update.
            request: Optional HTTP request for logging IP and user agent.

        Returns:
            TopUpRequest: The updated top-up request instance.

        Raises:
            ValueError: If the top-up request is not in 'pending' status —
                        only pending requests can be edited.
            TopUpRequest.DoesNotExist: If no matching top-up request is found.
        """
        with transaction.atomic():
            topup = (
                self.manager.select_for_update()
                .select_related(
                    "pettycash_account", "requested_by", "status", "event_type"
                )
                .get(id=topup_id)
            )

            if topup.status.code != "pending":
                raise ValueError(
                    f"Cannot edit a top-up request that is already '{topup.status.name}'."
                )

            old_values = {
                field: str(getattr(topup, field, None)) for field in data.keys()
            }

            for field, value in data.items():
                setattr(topup, field, value)

            new_values = {
                field: str(getattr(topup, field, None)) for field in data.keys()
            }

            topup.save(update_fields=list(data.keys()) + ["updated_at"])

            TransactionLogService.log(
                entity=topup,
                event_code="topup_requested",  # still in requested stage — no workflow change
                triggered_by=triggered_by,
                message=f'Top-up request "{topup.id}" updated',
                ip_address=request.META.get("REMOTE_ADDR") if request else None,
                metadata={
                    "topup_id": str(topup.id),
                    "account_id": str(topup.pettycash_account.id),
                    "account_name": topup.pettycash_account.name,
                    "changed_fields": list(data.keys()),
                    "old_values": old_values,
                    "new_values": new_values,
                    "updated_by_id": str(triggered_by.id),
                    "updated_by_email": triggered_by.email,
                    "updated_by_role": triggered_by.role.name,
                    "action": "update",
                },
            )

    def deactivate_top_up_request(
        self, topup_id: str, triggered_by: User, request=None
    ):
        """
        Soft deletes a top-up request by setting is_active to False.

        Args:
            topup_id (str): The ID of the top-up request to deactivate.
            triggered_by (User): The user performing the deactivation.
            request: Optional HTTP request for logging IP and user agent.

        Returns:
            TopUpRequest: The updated top-up request instance.
        """
        topup = self.manager.get(id=topup_id)
        inactive_status = Status.objects.get(code="INACT")
        inactive_event = EventTypes.objects.get(code="topup_deactivated")

        topup.is_active = False
        topup.status = inactive_status
        topup.event_type = inactive_event
        topup.save(
            update_fields=["is_active", "updated_at", "status_id", "event_type_id"]
        )

        TransactionLogService.log(
            entity=topup,
            event_code="topup_deactivated",
            triggered_by=triggered_by,
            status_code="INACT",
            message=f'Top-up request "{topup.id}" deactivated',
            ip_address=request.META.get("REMOTE_ADDR") if request else None,
            metadata={
                "topup_id": str(topup.id),
                "account_id": str(topup.pettycash_account.id),
                "account_name": topup.pettycash_account.name,
                "changed_fields": ["is_active", "status"],
                "old_values": {"is_active": True, "status.code": "active"},
                "new_values": {"is_active": False, "status.code": "inactive"},
                "deactivated_by_id": str(triggered_by.id),
                "deactivated_by_email": triggered_by.email,
                "deactivated_by_role": triggered_by.role.name,
                "action": "deactivate",
            },
        )

        return topup

    def disburse_top_up_request(self, topup_id: str, triggered_by: User, request=None):
        """
            Disburses an approved top-up by crediting the petty cash account balance.
        Automatically triggers another top-up check after balance changes.

        Raises:
            ValueError: If the top-up request is not in 'approved' status.
        """
        topup = self.get_by_id(topup_id)

        if topup.status.code != "approved":
            raise ValueError(
                f"Cannot disburse a request that is '{topup.status.name}'. Must be 'approved'."
            )

        account = topup.pettycash_account
        previous_balance = account.current_balance

        # increment on the current balance the topup amount
        account.current_balance += topup.amount
        account.save(update_fields=["current_balance", "updated_at"])

        complete_status = Status.objects.get(code="complete")
        event_type = EventTypes.objects.get(code="topup_disbursed")

        topup.status = complete_status
        topup.event_type = event_type

        topup.save(update_fields=["status_id", "event_type_id", "updated_at"])

        TransactionLogService.log(
            entity=topup,
            event_code="topup_disbursed",
            triggered_by=triggered_by,
            message=f'Top-up of {topup.amount} disbursed to "{account.name}"',
            ip_address=request.META.get("REMOTE_ADDR") if request else None,
            metadata={
                "topup_id": str(topup.id),
                "account_id": str(account.id),
                "account_name": account.name,
                "amount": str(topup.amount),
                "previous_balance": str(previous_balance),
                "new_balance": str(account.current_balance),
                "disbursed_by_id": str(triggered_by.id),
                "disbursed_by_email": triggered_by.email,
                "disbursed_by_role": triggered_by.role.name,
                "action": "disburse",
            },
        )
        
        return topup



# -----------------------------------------------------------------------------
# DISBURSEMENT RECONSILIATION SERVICE
# -----------------------------------------------------------------------------
class DisbursementReconciliationService(ServiceBase):
    manager = DisbursementReconciliation.objects

    def get_by_status(self, status_code):
        return self.manager.filter(status__code=status_code)

    def get_by_submitter(self, user_id):
        return self.manager.filter(submitted_by__id=user_id)

    def get_by_expense_request(self, expense_request_id):
        return self.manager.filter(expense_request__id=expense_request_id).first()
