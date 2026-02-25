from django.db import models
from base.models import BaseModel,GenericBaseModel,Status, Category
from department.models import Department
from django.utils.translation import gettext_lazy as _
from users.models import User
from finance.default import (get_default_expense_category, get_default_expense_submitted_event, get_default_pending_status, get_default_topup_requested_event)
from audit.models import EventTypes


# Create your models here.
class PettyCashAccount(GenericBaseModel):

    is_active = models.BooleanField(default=True,verbose_name=_('Is Active'))
    account_type = models.CharField(default='mpesa', max_length=20, blank=True, verbose_name=_('Account Type'))
    mpesa_phone_number = models.CharField(max_length=15, blank=True, verbose_name=_('Phone number'))
    current_balance = models.DecimalField(max_digits=8,default=0, decimal_places=2, blank=True,verbose_name=_('Current balance'))
    minimum_threshold = models.DecimalField(max_digits=8, default=0, decimal_places=2,blank=True, verbose_name=_('Minimum Threshold'))


    class Meta:
        db_table = 'pettycash_account'
        verbose_name = _('PettyCash account')
        verbose_name_plural = _('PettyCash accounts')
        ordering = ['-created_at']


class ExpenseRequest(BaseModel):

    class ExpenseType(models.TextChoices):
        REIMBURSEMENT = 'reimbursement', _('Reimbursement')
        DISBURSEMENT = 'disbursement', _('Disbursement')


    employee = models.ForeignKey(
        User,
        on_delete=models.PROTECT,
        related_name='expense_request',
        verbose_name=_('Employee')
    )
    category = models.ForeignKey(
        Category,
        on_delete=models.PROTECT,
        default=get_default_expense_category, # auto resolves the category
        related_name='expense_requests',
        verbose_name=_('Category')
    )

    expense_type = models.CharField(
        max_length=20,
        choices=ExpenseType.choices,
        default=ExpenseType.REIMBURSEMENT,
        verbose_name=_('Expense Type')
    )
    
    event_type = models.ForeignKey(          # tracks current workflow stage
        EventTypes,
        on_delete=models.PROTECT,
        related_name='expense_requests',
        null=True, blank=True,
        default=get_default_expense_submitted_event,   # auto-resolves to 'expense_submitted'
        verbose_name=_('Event Type')
    )

    # REMOVED: assigned_to — FOs see all requests via role-based filtering in the service layer.
    #decision_by and decision_at —  moved to metadata

    status = models.ForeignKey(
        Status,
        on_delete=models.PROTECT,
        related_name='expense_requests',
        null=True, blank=True,
        default=get_default_pending_status,
        verbose_name='Status'
    )
    
    # Removed: department (derive from employee.department)

    # core data
    title = models.CharField(max_length=100, blank=True, verbose_name=_('Title'))
    mpesa_phone = models.CharField(max_length=20, blank=True, verbose_name=_('M-Pesa Phone'))
    description = models.TextField(blank=True, verbose_name=_('Description'))
    amount = models.DecimalField(max_digits=8, decimal_places=2, verbose_name=_('Amount'))
    receipt = models.FileField(upload_to='receipts/%Y/%m/%d/',null=True, blank=True, verbose_name=_('Receipt'))

    metadata = models.JSONField(default=dict, blank=True, verbose_name=_('Metadata'))  # store approved_by, timestamps, comments, etc.

    class Meta:
        db_table = 'expense_requests'
        verbose_name = _('Expense Request')
        verbose_name_plural = _('Expense Requests')
        ordering = ['-created_at']

    def __str__(self):
         return f"{self.title or 'No Title'} - {self.employee.email}"


class TopUpRequest(BaseModel):
    pettycash_account = models.ForeignKey(
        PettyCashAccount,
        on_delete=models.PROTECT,
        related_name='topup_requests',
        verbose_name=_('Petty Cash Account')
    )
    status = models.ForeignKey(
        Status,
        on_delete=models.PROTECT,
        default=get_default_pending_status,
        related_name='topup_requests',
        verbose_name=_('Status')
    )
    requested_by = models.ForeignKey(
        User,
        on_delete=models.PROTECT,
        related_name='requested_topups',
        verbose_name=_('Requested by')
    )
    decision_by = models.ForeignKey(
        User,
        on_delete=models.PROTECT,
        related_name='approved_topups',
        null=True,
        blank=True,
        default=None,
        verbose_name=_('Approved by')
    )
    event_type = models.ForeignKey(          # tracks current workflow stage
        EventTypes,
        on_delete=models.PROTECT,
        related_name='topup_requests',
        null=True, blank=True,
        default=get_default_topup_requested_event,     # auto-resolves to 'topup_requested'
        verbose_name=_('Event Type')
    )

    metadata = models.JSONField(default=dict, blank=True, verbose_name=_('Metadata'))
     # reason for REQUESTING the top-up e.g. "Balance too low for upcoming expenses"
    request_reason = models.CharField(max_length=255, blank=True, null=True, verbose_name=_('Request Reason'))

    # reason for the DECISION e.g. "Approved — end of month budget available" or "Rejected — insufficient budget"
    decision_reason = models.CharField(max_length=255, blank=True, verbose_name=_('Decision Reason'))
    amount = models.DecimalField(max_digits=15, decimal_places=2, default=0, verbose_name=_('Amount'))
    is_auto_triggered = models.BooleanField(default=False)

    class Meta:
        db_table = 'topup_requests'
        verbose_name = _('Top-up Request')
        verbose_name_plural = _('TopUp Requests')
        ordering = ['-created_at']


class DisbursementReconciliation(BaseModel):
    """
    Tracks the reconciliation of disbursement-type expense requests.
    """

    expense_request = models.OneToOneField(
        ExpenseRequest,
        on_delete=models.CASCADE,
        related_name='disbursement_reconciliation',
        verbose_name='Expense Request'
    )

    submitted_by = models.ForeignKey(
        User,
        on_delete=models.PROTECT,
        related_name='submitted_disbursement_reconciliations',
        verbose_name='Submitted by'
    )

    submitted_at = models.DateTimeField(
        auto_now_add=True,
        verbose_name='Submitted at'
    )

    approved_by = models.ForeignKey(
        User,
        on_delete=models.PROTECT,
        related_name='approved_disbursement_reconciliations',
        verbose_name='Approved by',
        null=True,
        blank=True
    )

    approved_at = models.DateTimeField(
        null=True,
        blank=True,
        verbose_name='Approved at'
    )

    status = models.ForeignKey(
        Status,
        on_delete=models.PROTECT,
        related_name='disbursement_reconciliations',
        null=True, blank=True,
        verbose_name='Status'
    )

    reconciled_amount = models.DecimalField(
        max_digits=15,
        decimal_places=2,
        null=True,
        blank=True,
        verbose_name='Reconciled Amount'
    )
    
    surplus_returned = models.DecimalField(
        max_digits=15,
        decimal_places=2,
        null=True,
        blank=True,
        default=0,
        verbose_name='Surplus Returned'
    )
    
    receipt = models.FileField(
        upload_to='reconciliation_receipts/%Y/%m/%d/',
        null=True,
        blank=True,
        verbose_name='Receipt'
    )

    comments = models.TextField(
        blank=True, null=True,
        verbose_name='Comments'
    )

    metadata = models.JSONField(
        default=dict,
        blank=True, null=True,
        verbose_name='Metadata'
    )

    class Meta:
        db_table = 'disbursement_reconciliations'
        verbose_name = 'Disbursement Reconciliation'
        verbose_name_plural = 'Disbursement Reconciliations'
        ordering = ['-submitted_at']

    def __str__(self):
        return f"Reconciliation for {self.expense_request.id} | Status: {self.status.name}"