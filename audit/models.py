from django.conf import settings
from django.db import models
from django.utils.translation import gettext_lazy as _
from base.models import GenericBaseModel,BaseModel,Status,Category
from users.models import User
from django.utils import timezone






class EventTypes(GenericBaseModel):
    status_code = models.CharField(max_length=30, blank=True,verbose_name=_('Status Code'))
    is_active = models.BooleanField(default=True)

    event_category = models.ForeignKey(
        Category,
        related_name='event_types',
        verbose_name=_('Event Category'),
        on_delete=models.PROTECT
    )

    # USAGE:
    # EventTypes.objects.get(code="expense_approved").event_category.name  → "expense"
    # EventCategory.objects.get(name="expense").event_types.all()    → QuerySet

    class Meta:
        db_table = 'event_types'
        verbose_name = _('Event Type')
        verbose_name_plural = _('Event Types')


# Create your models here.
class TransactionLogBase(BaseModel):
    updated_at = None

    user_ip_address = models.GenericIPAddressField(
        editable=False,
        null=True,
        blank=True,
        verbose_name=_("User IP Address")
    )
    event_type = models.ForeignKey(
        EventTypes,
        on_delete=models.PROTECT,
        related_name='transaction_logs',
        verbose_name=_('Event Type')
    )

    event_message = models.CharField(max_length=255,blank=True, verbose_name=_('Event Message'))
    status = models.ForeignKey(Status, max_length=20, on_delete=models.PROTECT, verbose_name=_('Status'))

    triggered_by = models.ForeignKey(
        User,
        on_delete=models.SET_NULL, #If a user is deleted: The triggered_by becomes NULL The triggered_by becomes NULL
        null=True, blank=True,
        related_name='transaction_logs',
        verbose_name=_('User')
    )


    metadata = models.JSONField(null=True, blank=True, verbose_name=_('Metadata'))
    entity_type = models.CharField(max_length=50,blank=True, verbose_name=_('Entity Type'))
    entity_id = models.CharField(max_length=100, blank=True, verbose_name=_('Entity ID'))
    created_at = models.DateTimeField(auto_now_add=True, verbose_name=_('Created At'))

    # USAGE:
    # log.event_type.code          → "expense_approved"
    # log.event_type.category.name → "expense"     (two joins, one query with select_related)
    # log.triggered_by             → User object or None
    # log.notifications.all()      → all notifications spawned from this log
    # user.triggered_logs.count()  → how many events this user has triggered

    class Meta:
        verbose_name = _('TransactionLog')
        verbose_name_plural = _('TransactionLogs')
        ordering = ['-created_at']
        db_table = 'transaction_logs'
        indexes = [
            models.Index(fields=['entity_type','entity_id']),
            models.Index(fields=['triggered_by'])
        ]

    def __str__(self):
        return f"{self.event_type} - {self.status}"






class Notifications(BaseModel):
    updated_at = None

    transaction_log = models.ForeignKey(
        TransactionLogBase,
        on_delete=models.PROTECT, # You cannot delete a log if notifications reference it
        related_name='notifications'  # → log.notifications.all()
    )

    recipient = models.ForeignKey(
        User,
        on_delete=models.PROTECT, #  You cannot delete a user if notifications exist
        related_name='notifications' # → user.notifications.all()   ← the user's inbox
    )

    class Channel(models.TextChoices):
        IN_APP = "in_app", _('In App')
        SMS = 'sms', _('SMS')
        EMAIL = 'email', _('Email')



    channel = models.CharField(max_length=20,choices=Channel, default=Channel.IN_APP, verbose_name=_('Channel'))
    is_read = models.BooleanField(default=False,verbose_name=_('Is read'))
    read_at = models.DateTimeField(null=True,blank=True,verbose_name=_('Read at'))

    # USAGE:
    # user.notifications.filter(is_read=False)
    #     .select_related("transaction_log__event_type",
    #                     "transaction_log__triggered_by")
    #
    # notif.transaction_log.triggered_by    → who caused this (NOT on Notification)
    # notif.transaction_log.event_type.code → "expense_approved"
    # notif.transaction_log.entity_id       → "1042"

    def save(self, *args, **kwargs):
        if self.is_read and not self.read_at:
            self.read_at = timezone.now()
        elif not self.is_read:
            self.read_at = None
        super().save(*args, **kwargs)

    def __str__(self):
        event = self.transaction_log.event_type.name
        entity = self.transaction_log.entity_id or "N/A"
        status = "Read" if self.is_read else "Unread"

        return f"{self.recipient.email} | {event} | Entity: {entity} | {status}"

    class Meta:
        db_table = 'notifications'
        ordering = ['-created_at']
        indexes = [
            models.Index(fields=['is_read', 'recipient', 'transaction_log'])
        ]