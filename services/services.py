from django.db.models import Manager
from typing import Type

from finance.models import PettyCashAccount, ExpenseRequest, TopUpRequest, DisbursementReconciliation
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
    def get_active_user_by_email(self,email):
        return self.manager.get(email=email,is_active=True)

    @staticmethod
    def update_last_login(user: User) ->User:
        from django.utils import timezone

        user.last_login = timezone.now()
        user.save(update_fields=['last_login'])
        return user

    @staticmethod
    def log_login(user: User, request) -> None:
        TransactionLogService().log(
            event_code='user_login_success',
            triggered_by=user,
            entity=user,
            status_code='ACT',
            message=f'{user.email} logged in successfully',
            ip_address=request.META.get('REMOTE_ADDR'),
            metadata={
                'user_id': str(user.id),
                'email': user.email,
                'role': user.role.name,
                'department': user.department.name if user.department else None,
                'user_agent': request.META.get('HTTP_USER_AGENT'),
                'device_type': 'mobile' if 'Mobile' in request.META.get('HTTP_USER_AGENT', '') else 'desktop',
                'ip_address': request.META.get('REMOTE_ADDR'),
                'forwarded_ip': request.META.get('HTTP_X_FORWARDED_FOR'),
                'login_method': 'email_password',
                'login_at': timezone.now().isoformat(),
            }
        )

class DepartmentService(ServiceBase):
    manager = Department.objects

    def get_active_departments(self):
        return self.manager.filter(is_active=True)

    def get_by_manager(self, user_id):
        return self.manager.filter(line_manager__id=user_id)

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
            status_code: str ='200',
            message: str = '',
            metadata: dict =None,
            ip_address: str = None
    ) -> TransactionLogBase:
        event_type = EventTypes.objects.get(code=event_code)
        status = Status.objects.get(code=status_code)

        return TransactionLogBase.objects.create(
            event_type=event_type,
            triggered_by=triggered_by,
            status=status,
            event_message = message,
            metadata = metadata or {},
            entity_type=entity.__class__.__name__, # "User", "ExpenseRequest" etc
            entity_id = str(entity.pk),
            user_ip_address=ip_address
        )

    @staticmethod
    def get_logs_for_entity(entity):
        """get all logs for a specific entity e.g. user, expense"""
        return TransactionLogBase.objects.filter(
            entity_type=entity.__class__.__name__,
            entity_id=str(entity.pk)
        ).select_related('event_type', 'triggered_by', 'status')

    @staticmethod
    def get_logs_by_event(event_code: str):
        """Get all logs for a specific event e.g all logins"""
        return TransactionLogBase.objects.filter(
            event_type__code=event_code
        ).select_related('event_type', 'triggered_by', 'status')

    @staticmethod
    def get_user_logs(user: User):
        """Everything a specific user has triggered"""
        return TransactionLogBase.objects.filter(
            triggered_by=user
        ).select_related('event_type', 'status')


class NotificationService(ServiceBase):
    manager = Notifications.objects

    def get_unread(self, user_id):
        return self.manager.filter(recipient__id=user_id, is_read=False)

    def get_by_recipient(self, user_id):
        return self.manager.filter(recipient__id=user_id)

    def mark_as_read(self, uuid):
        return self.filter(id=uuid).update(is_read=True)

class PettyCashAccountService(ServiceBase):
    manager = PettyCashAccount.objects

    def get_active_accounts(self):
        return self.manager.filter(is_active=True)

    def get_below_threshold(self):
        from django.db.models import F
        return self.manager.filter(current_balance__lte=F('minimum_threshold'))


class ExpenseRequestService(ServiceBase):
    manager = ExpenseRequest.objects

    def get_by_employee(self, user_id):
        return self.manager.filter(employee__id=user_id)

    def get_by_status(self, status_code):
        return self.manager.filter(status__code=status_code)

    def get_by_department(self, department_id):
        return self.manager.filter(department__id=department_id)

    def get_assigned_to(self, user_id):
        return self.manager.filter(assigned_to__id=user_id)

    def get_by_expense_type(self, expense_type):
        return self.manager.filter(expense_type=expense_type)


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
