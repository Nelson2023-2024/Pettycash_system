from django.db import models
from django.utils.translation import gettext_lazy as _
import uuid

# Create your models here.
class BaseModel(models.Model):
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False, unique=True)
    created_at = models.DateTimeField(auto_now_add=True, verbose_name=_('Date created'))
    updated_at = models.DateTimeField(auto_now=True, verbose_name=_('Date modified'))

    class Meta:
        abstract = True



class GenericBaseModel(BaseModel):
    name = models.CharField(max_length=100, verbose_name=_('Name'))
    description = models.CharField(max_length=100, blank=True, verbose_name=_('Description'))

    class Meta:
        abstract = True