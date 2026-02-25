from django.db import transaction
from django.db.models import Manager, QuerySet
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

from django.db import transaction, IntegrityError
import logging

logger = logging.getLogger(__name__)


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
            raise TransactionLogError(
                f"Failed to create transaction log for event '{event_code}': {str(e)}"
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

    @staticmethod
    def notify(
        transaction_log, recipient, channel: str = Notifications.Channel.IN_APP
    ) -> Notifications:
        """
         Creates a single notification tied to a transaction log.
        This is the core reusable method called from any service after
        a TransactionLogService.log() call.

        Args:
            transaction_log: The TransactionLogBase instance just created.
            recipient (User): The user who should receive the notification.
            channel (str): Delivery channel — in_app, sms, or email. Defaults to in_app.

        Returns:
            Notifications: The created notification instance.

        """
        return Notifications.objects.create(
            transaction_log=transaction_log, recipient=recipient, channel=channel
        )

    @staticmethod
    def notify_many(
        transaction_log, recipient, channel: str = Notifications.Channel.IN_APP
    ):
        """
        Creates notifications for multiple recipients from a single transaction log.
        Uses bulk_create for efficiency.
        For example, when an expense is submitted, notify all Finance Officers at once.

        Args:
            transaction_log: The TransactionLogBase instance just created.
            recipients (list[User]): List of users to notify.
            channel (str): Delivery channel for all recipients. Defaults to in_app.

        Returns:
            list[Notifications]: The created notification instances.

        :param transaction_log:
        :param recipient:
        :param channel:
        :return:
        """
        return Notifications.objects.bulk_create(
            [
                Notifications(
                    transaction_log=transaction_log,
                    recipient=recipient,
                    channel=channel,
                )
            ]
        )

    def list_auth_user_notifications(self, auth_user: User):
        """

        Retrieves all notifications for the authenticated user ordered by
        most recent first, with transaction log and event type pre-fetched.

        Args:
            auth_user (User): The currently authenticated user.

        Returns:
            QuerySet: All Notifications for the user with related fields joined.

        """
        return self.manager.filter(id=auth_user).select_related(
            "transaction_log__event_type", "transaction_log__triggered_by"
        )

    def get_unread_count(self, auth_user: User):
        """
        Returns the count of unread notifications for the authenticated user.
        Used for the notification badge/counter in the UI.

        Args:
            auth_user (User): The currently authenticated user.

        Returns:
            int: Number of unread notifications.
        """
        return self.manager.filter(id=auth_user, is_read=False).count()

    def mark_as_read(self, notification_id: str, auth_user: User):
        """
        Marks a single notification as read.
        Scoped to the authenticated user to prevent one user marking
        another user's notifications as read.

        Args:
            notification_id (str): The UUID of the notification to mark as read.
            auth_user (User): The currently authenticated user.

        Returns:
            Notifications: The updated notification instance.

        Raises:
            Notifications.DoesNotExist: If no matching notification found for this user.
        """
        notification = self.manager.get(
            id=notification_id, is_read=False, recipient=auth_user
        )
        notification.is_read = True
        notification.save(update_fields=["is_read", "read_at"])
        return notification

    def get_mark_all_as_read(self, auth_user: User):
        """
          Marks all unread notifications as read for the authenticated user.
        Uses bulk update for efficiency — bypasses model save() so read_at
        is set explicitly here rather than relying on the model.

        Args:
            auth_user (User): The currently authenticated user.

        Returns:
            int: Number of notifications updated.

        """
        return self.manager.filter(recipient=auth_user, is_read=False).update(
            is_read=True, read_at=timezone.now()
        )


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
        expense_type: str,
        receipt=None,
    ):
        """
        Creates a new expense request for the given employee.
        Category, status, and assigned_to are auto-resolved via defaults in the models.
        """
        expense = self.manager.create(
            employee=employee,
            expense_type=expense_type,
            title=title,
            mpesa_phone=mpesa_phone,
            description=description,
            amount=amount,
            receipt=receipt,
        )
        TransactionLogService.log(
            entity=expense,
            event_code="expense_submitted",
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
        return self.manager.filter(is_active=True).select_related("employee", "status")

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
            "status"
        )

    def get_all_pending_for_fo(self):
        """
        Retrieves all active, pending expense requests visible to any Finance Officer.
        No assignment check needed — role-based access is handled at the view/permission layer.
        """
        return self.manager.filter(
            is_active=True, status__code="pending"
        ).select_related("employee", "status")

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
                self.manager.select_for_update(
                    of=("self",)
                )  # Lock only the main table row — not the joined tables.
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

    def approve_or_reject(
        self,
        request,
        expense_id: str,
        decision: str,
        triggered_by: User,
        reason: str = None,
    ):
        """
        action: 'approve' or 'reject'
        FO approves or rejects a pending expense request.
        """

        with transaction.atomic():
            expense = (
                self.manager.select_for_update(of=("self",))
                .select_related("status")
                .get(id=expense_id, is_active=True)
            )

            if expense.status.code != "pending":
                raise ValueError(
                    f"Only pending requests can be approved or rejected. Current status: {expense.status.code}"
                )

            new_status = Status.objects.get(code=decision)  # 'approved' or 'rejected'
            event_code = (
                f"expense_{decision}"  # 'expense_approved' or 'expense_rejected'
            )

            expense.status = new_status

            expense.metadata.update(
                {
                    "decision": decision,
                    "decision_by": str(triggered_by.id),
                    "decision_by_email": triggered_by.email,
                    "decision_at": timezone.now().isoformat(),
                    "decision_reason": reason or "",
                }
            )

            expense.save(update_fields=["status", "metadata", "updated_at"])

            TransactionLogService.log(
                entity=expense,
                event_code=event_code,
                triggered_by=triggered_by,
                message=f'Expense request "{expense.title}" {decision} by {triggered_by.email}',
                ip_address=request.META.get("REMOTE_ADDR") if request else None,
                metadata={
                    "expense_id": str(expense.id),
                    "title": expense.title,
                    "amount": str(expense.amount),
                    "expense_type": expense.expense_type,
                    "decision": decision,
                    "decision_reason": reason or "",
                    "decision_by_id": str(triggered_by.id),
                    "decision_by_email": triggered_by.email,
                    "employee_id": str(expense.employee.id),
                    "employee_email": expense.employee.email,
                    "action": decision,
                },
            )

            return expense

    def disburse(self, request, expense_id: str, triggered_by: User):
        """
        Marks an approved expense request as disbursed.
            - Reimbursement: disbursed = completed, no reconciliation needed.
            - Disbursement: disbursed = cash sent, reconciliation record auto-created.
        """
        with transaction.atomic():
            expense = (
                self.manager.select_for_update(of=("self",))
                .select_related("status", "employee")
                .get(id=expense_id, is_active=True)
            )

            if expense.status.code != "approved":
                raise ValueError(
                    f"Only approved requests can be disbursed. Current status: {expense.status.code}"
                )

            disbursed_status = Status.objects.get(code="disbursed")
            expense.status = disbursed_status
            expense.metadata.update(
                {
                    "disbursed_by": str(triggered_by.id),
                    "disbursed_by_email": triggered_by.email,
                    "disbursed_at": timezone.now().isoformat(),
                }
            )

            expense.save(update_fields=["status", "metadata", "updated_at"])

            # Only disbursement-type needs reconciliation — reimbursement already had receipt at submission
            if expense.expense_type == ExpenseRequest.ExpenseType.DISBURSEMENT:
                DisbursementReconciliation.objects.create(
                    expense_request=expense,
                    submitted_by=expense.employee,
                    status=Status.objects.get(code="pending"),
                    total_amount=expense.amount,
                )

            TransactionLogService.log(
                entity=expense,
                event_code="expense_disbursed",
                triggered_by=triggered_by,
                message=f'Expense request "{expense.title}" disbursed by {triggered_by.email}',
                ip_address=request.META.get("REMOTE_ADDR") if request else None,
                metadata={
                    "expense_id": str(expense.id),
                    "title": expense.title,
                    "amount": str(expense.amount),
                    "expense_type": expense.expense_type,
                    "disbursed_by_id": str(triggered_by.id),
                    "disbursed_by_email": triggered_by.email,
                    "employee_id": str(expense.employee.id),
                    "employee_email": expense.employee.email,
                    "action": "disburse",
                },
            )

            return expense
        # REIMBURSEMENT: submitted → pending → approved → disbursed ✅ (closed)
        # DISBURSEMENT:  submitted → pending → approved → disbursed → reconciliation pending → under_review → completed ✅


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
        decision: str,  # 'approved' or 'rejected'
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
        try:
            with transaction.atomic():
                topup = (
                    TopUpRequest.objects.select_for_update()
                    .select_related("status")
                    .get(id=topup_id, is_active=True)
                )

            # Idempotency check
            if topup.status.code == decision:
                return topup

            status = Status.objects.get(code=decision)
            event_code = (
                "topup_approved" if decision == "approved" else "topup_rejected"
            )
            event_type = EventTypes.objects.get(code=event_code)
            decision_at = timezone.now()

            topup.status = status
            topup.event_type = event_type
            topup.decision_by = triggered_by
            topup.decision_reason = decision_reason or ""
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
                status_code=decision,  # or a relevant status
                message=f"Top-up request {decision} for {topup.amount}",
                ip_address=request.META.get("REMOTE_ADDR") if request else None,
                metadata={
                    "topup_id": str(topup.id),
                    "account_id": str(topup.pettycash_account.id),
                    "decision_reason": decision_reason,
                    "decision_at": decision_at.isoformat(),
                },
            )

            return topup
        except IntegrityError as e:
            logger.error(f"IntegrityError in decide_top_up_request: {e}", exc_info=True)
            # Re-raise as a more specific exception or let the controller handle it
            raise

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
                self.manager.select_for_update(of=("self",))
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
        # If already complete – just return (idempotent)
        if topup.status.code == "complete":
            return topup

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

    def get_my_pending(self, auth_user: User):
        """
        Retrieves all pending reconciliations for the authenticated employee.
        These are disbursements where the employee has not yet submitted receipts.

        Args:
            auth_user (User): The currently authenticated employee.

        Returns:
            QuerySet: DisbursementReconciliation instances where submitted_by matches
            auth_user and status is pending, with expense_request and status pre-fetched.
        """
        return self.manager.filter(
            submitted_by=auth_user, status__code="pending"
        ).select_related("expense_request", "status")

    def get_all_under_review(self):
        """
        Retrieves all reconciliations that have been submitted by employees
        and are awaiting Finance Officer review.

        Returns:
            QuerySet: DisbursementReconciliation instances with status under_review,
            with expense_request, submitted_by, and status pre-fetched.
        """
        return self.manager.filter(status__code="under_review").select_related(
            "expense_request", "submitted_by", "status"
        )

    def get_by_id(self, reconciliation_id: str):
        """
        Retrieves a single reconciliation record by its ID.
        Used for detail views on both the employee and FO side.

        Args:
            reconciliation_id (str): The UUID of the reconciliation record.

        Returns:
            DisbursementReconciliation: The matching instance with related fields pre-fetched.

        Raises:
            DisbursementReconciliation.DoesNotExist: If no matching record is found.
        """
        return self.manager.select_related(
            "expense_request", "submitted_by", "approved_by", "status"
        ).get(id=reconciliation_id)

    def submit_receipt(
        self,
        request,
        reconsiliation_id: str,
        submitted_by: User,
        comments: str,
        reconciled_amount: float,
        surplus_returned: float,
        receipt=None,
    ):
        """


             Employee submits receipts after cash has been disbursed.
        Employee reports how much they spent (reconciled_amount) and
        how much they are returning (surplus_returned) if they didn't use it all.
        Transitions reconciliation status from pending -> under_review.

        Args:
            request: The HTTP request object for IP logging.
            reconciliation_id (str): The UUID of the reconciliation to update.
            receipt: The uploaded receipt file.
            submitted_by (User): The employee submitting the receipts.
            reconciled_amount (Decimal): Amount the employee actually spent, backed by the receipt.
            surplus_returned (Decimal, optional): Cash being returned if less than disbursed amount was spent.
            comments (str, optional): Any notes from the employee about the expense.

        Returns:
            DisbursementReconciliation: The updated reconciliation instance.

        Raises:
            ValueError: If the reconciliation is not in pending status.
            ValueError: If reconciled_amount exceeds the original disbursed amount.
            DisbursementReconciliation.DoesNotExist: If no matching record is found.
        """

        with transaction.atomic():
            reconciliation = (
                self.manager.select_for_update(of=("self",))
                .select_related("status", "expense_request", "submitted_by")
                .get(id=reconsiliation_id, is_active=True)
            )

            if reconciliation.status.code != "pending":
                raise ValueError(
                    f"Receipts already submitted. Current status: {reconciliation.status.code}"
                )

            disbursed_amount = reconciliation.expense_request.amount

            if reconciled_amount > disbursed_amount:
                raise ValueError(
                    f"Reconciled amount {reconciled_amount} cannot exceed "
                    f"the disbursed amount of {disbursed_amount}."
                )

            under_review_status = Status.objects.get(code="under_review")
            reconciliation.status = under_review_status
            reconciliation.comments = comments
            reconciliation.receipt = receipt
            reconciliation.surplus_returned = surplus_returned
            reconciliation.reconciled_amount = reconciled_amount
            reconciliation.save(
                update_fields=[
                    "receipt",
                    "reconciled_amount",
                    "surplus_returned",
                    "comments",
                    "status",
                    "updated_at",
                ]
            )

            TransactionLogService.log(
                entity=reconciliation,
                event_code="expense_reconciliation_submitted",
                triggered_by=submitted_by,
                message=f"Reconciliation receipts submitted for expense {reconciliation.expense_request.id}",
                ip_address=request.META.get("REMOTE_ADDR") if request else None,
                metadata={
                    "reconciliation_id": str(reconciliation.id),
                    "expense_request_id": str(reconciliation.expense_request.id),
                    "disbursed_amount": str(disbursed_amount),
                    "reconciled_amount": str(reconciled_amount),
                    "surplus_returned": str(surplus_returned or 0),
                    "submitted_by_id": str(submitted_by.id),
                    "submitted_by_email": submitted_by.email,
                    "action": "submit_receipts",
                },
            )

            return reconciliation

    def review(
        self,
        request,
        reconciliation_id: str,
        decision: str,
        triggered_by: User,
        comments: str = None,
    ):
        """
             Finance Officer reviews a submitted reconciliation and either approves or rejects it.

        On approval (completed):
            - Reconciliation status moves to completed.
            - Parent expense request is also marked as completed.

        On rejection (rejected):
            - Reconciliation status moves back to pending.
            - Employee will be expected to resubmit with corrections.
            - reconciled_amount and surplus_returned are cleared back to null
              since the submission was not accepted.
            - receipt is cleared so the employee must re-upload.

        Note:
            'rejected' here is NOT terminal — it sends the reconciliation back
            to the employee for correction and resubmission. Terminal rejection
            only happens at the expense request level before any cash goes out.

        Args:
            request: The HTTP request object for IP logging.
            reconciliation_id (str): The UUID of the reconciliation to review.
            decision (str): 'completed' to approve or 'rejected' to send back to employee.
            triggered_by (User): The Finance Officer performing the review.
            comments (str, optional): FO feedback. Should always be provided on rejection
                so the employee knows what to fix.

        Returns:
            DisbursementReconciliation: The updated reconciliation instance.

        Raises:
            ValueError: If decision is not 'completed' or 'rejected'.
            ValueError: If reconciliation is not currently under_review.
            DisbursementReconciliation.DoesNotExist: If no matching record is found.


        """
        if decision not in ["completed", "rejected"]:
            raise ValueError("Decision must be 'completed' or 'rejected'.")

        with transaction.atomic():
            reconciliation = (
                self.manager.select_for_update(of=("self",))
                .select_related("status", "submitted_by", "expense_request")
                .get(id=reconciliation_id, is_active=True)
            )

            if reconciliation.status.code != "under_review":
                raise ValueError(
                    f"Only under_review reconciliations can be reviewed. "
                    f"Current status: {reconciliation.status.code}"
                )

            if decision == "completed":
                new_status = Status.boject.get(code="completed")
                reconciliation.status = new_status
                reconciliation.approved_by = (triggered_by,)
                reconciliation.approved_at = timezone.now().isoformat()
                reconciliation.comments = comments
                reconciliation.metadata.update(
                    {
                        "reviewed_by": str(triggered_by.id),
                        "reviewed_by_email": triggered_by.email,
                        "reviewed_at": timezone.now().isoformat(),
                        "decision": decision,
                        "comments": comments or "",
                    }
                )
                reconciliation.save(
                    update_fields=[
                        "status",
                        "approved_by",
                        "approved_at",
                        "comments",
                        "metadata",
                        "updated_at",
                    ]
                )

                # close the parent expense request

                expense = reconciliation.expense_request
                expense.status = new_status
                expense.metadata.update(
                    {
                        "completed_by": str(triggered_by.id),
                        "completed_by_email": triggered_by.email,
                        "completed_at": timezone.now().isoformat(),
                    }
                )

                expense.save(update_fields=["status", "metadata", "updated_at"])
            else:
                pendind_status = Status.objects.get(code="pending")
                reconciliation.status = pendind_status
                reconciliation.approved_by = None
                reconciliation.approved_at = None
                reconciliation.reconciled_amount = (
                    None  # clear — employee must resubmit
                )
                reconciliation.surplus_returned = None  # clear — employee must resubmit
                reconciliation.receipt = None  # clear — employee must re-upload
                reconciliation.comments = comments or ""
                reconciliation.metadata.update(
                    {
                        "reviewed_by": str(triggered_by.id),
                        "reviewed_by_email": triggered_by.email,
                        "reviewed_at": timezone.now().isoformat(),
                        "decision": decision,
                        "rejection_reason": comments or "",
                    }
                )
                reconciliation.save(
                    update_fields=[
                        "status",
                        "approved_by",
                        "approved_at",
                        "reconciled_amount",
                        "surplus_returned",
                        "receipt",
                        "comments",
                        "metadata",
                        "updated_at",
                    ]
                )
        TransactionLogService.log(
            entity=reconciliation,
            event_code=(
                "expense_completed"
                if decision == "completed"
                else "expense_reconciliation_submitted"
            ),
            triggered_by=triggered_by,
            message=f"Reconciliation {decision} by {triggered_by.email} for expense {reconciliation.expense_request.id}",
            ip_address=request.META.get("REMOTE_ADDR") if request else None,
            metadata={
                "reconciliation_id": str(reconciliation.id),
                "expense_request_id": str(reconciliation.expense_request.id),
                "decision": decision,
                "reviewed_by_id": str(triggered_by.id),
                "reviewed_by_email": triggered_by.email,
                "employee_id": str(reconciliation.submitted_by.id),
                "employee_email": reconciliation.submitted_by.email,
                "comments": comments or "",
                "action": decision,
            },
        )
        return reconciliation
