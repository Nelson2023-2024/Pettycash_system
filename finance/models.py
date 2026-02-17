from django.db import models
from base.models import BaseModel,GenericBaseModel,Status, Category
from django.utils.translation import gettext_lazy as _
from users.models import User


# Create your models here.
class PettyCashAccount(GenericBaseModel):

    is_active = models.BooleanField(default=True,verbose_name=_('Is Active'))
    account_type = models.CharField(default='mpesa', max_length=20, blank=True, verbose_name=_('Account Type'))
    mpesa_phone_number = models.CharField(max_length=15, blank=True, verbose_name=_('Phone number'))
    current_balance = models.DecimalField(max_digits=6,default=0, decimal_places=2, blank=True,verbose_name=_('Current balance'))
    minimum_threshold = models.DecimalField(max_digits=6, default=0, decimal_places=2,blank=True, verbose_name=_('Minimum Threshold'))


    class Meta:
        db_table = 'pettycash_account'
        verbose_name = _('PettyCash account')
        verbose_name_plural = _('PettyCash accounts')
        ordering = ['-created_at']


class ExpenseRequest(GenericBaseModel):
    name = None

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
        related_name='expense_requests',
        verbose_name=_('Category')
    )

    expense_type = models.CharField(
        max_length=20,
        choices=ExpenseType.choices,
        default=ExpenseType.REIMBURSEMENT,
        verbose_name=_('Expense Type')
    )

    assigned_to = models.ForeignKey(
        User,
        on_delete=models.PROTECT,
        related_name='assigned_expense_requests',
        verbose_name=_('Assigned To'),
        null=True, blank=True,  # optional at creation
    )

    # core data
    title = models.CharField(max_length=100, blank=True, verbose_name=_('Title'))
    mpesa_phone = models.CharField(max_length=20, blank=True, verbose_name=_('M-Pesa Phone'))
    description = models.TextField(blank=True, verbose_name=_('Description'))
    amount = models.DecimalField(max_digits=15, decimal_places=2, verbose_name=_('Amount'))
    receipt_url = models.JSONField(default=list, blank=True, verbose_name=_('Receipt URLs'))

    metadata = models.JSONField(default=dict, blank=True, verbose_name=_('Metadata'))  # store approved_by, timestamps, comments, etc.

    class Meta:
        db_table = 'expense_requests'
        verbose_name = _('Expense Request')
        verbose_name_plural = _('Expense Requests')
        ordering = ['-created_at']

    def __str__(self):
        assigned = self.assigned_to.email if self.assigned_to else "Unassigned"
        return f"{self.title or 'No Title'} - {self.employee.email} | {assigned}"


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
        related_name='topup_requests',
        verbose_name=_('Status')
    )
    requested_by = models.ForeignKey(
        User,
        on_delete=models.PROTECT,
        related_name='requested_topups',
        verbose_name=_('Requested by')
    )
    approved_by = models.ForeignKey(
        User,
        on_delete=models.PROTECT,
        related_name='approved_topups',
        null=True,
        default=None,
        verbose_name=_('Approved by')
    )

    metadata = models.JSONField(default=dict, blank=True, verbose_name=_('Metadata'))
    reason = models.CharField(max_length=100, blank=True, verbose_name=_('Reason'))

    class Meta:
        db_table = 'topup_requests'
        verbose_name = _('Top-up Request')
        verbose_name_plural = _('TopUp Requests')
        ordering = ['-created_at']
