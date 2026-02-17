from django.db import models
from base.models import BaseModel,GenericBaseModel,Status, Category
from django.utils.translation import gettext_lazy as _
from users.models import User


# Create your models here.
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

    # core data
    title = models.CharField(max_length=100, blank=True, verbose_name=_('Title'))
    mpesa_phone = models.CharField(max_length=20, blank=True, verbose_name=_('M-Pesa Phone'))
    description = models.TextField(blank=True, verbose_name=_('Description'))
    amount = models.DecimalField(max_digits=15, decimal_places=2, verbose_name=_('Amount'))
    receipt_url = models.JSONField(default=list, blank=True, verbose_name=_('Receipt URLs'))

    class Meta:
        db_table = 'expense_requests'
        verbose_name = _('Expense Request')
        verbose_name_plural = _('Expense Requests')
        ordering = ['-created_at']

    def __str__(self):
        return f"{self.title} - {self.employee.email}"
