from django.db import models
from django.utils.translation import gettext_lazy as _
from base.models import GenericBaseModel

# Create your models here.
class Department(GenericBaseModel):
    # e.g., 'FIN', 'HR', 'OPS'
    code = models.CharField(max_length=20, unique=True, verbose_name=_('Code'))
    is_active = models.BooleanField(default=True)

    # Points to the Manager (from the users app)
    line_manager = models.ForeignKey(
        'users.User',
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name='managed_departments',
        verbose_name=_('Line Manager')
    )

    class Meta:
        db_table = 'departments'
        verbose_name = _('Department')
        verbose_name_plural = _('Departments')