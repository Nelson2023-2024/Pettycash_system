from django.db import models
from django.contrib.auth.models import BaseUserManager, AbstractBaseUser, PermissionsMixin
from base.models import BaseModel
from django.utils.translation import gettext_lazy as _

# Create your models here.
class UserManager(BaseUserManager):
    def create_user(self, email, password=None, **extra_fields):
        # validation error when we dont pass email later
        if not email: raise ValueError("Users must have an email address")
        email = self.normalize_email(email) # Normalize the email address by lowercasing the domain part of it.
        # It refers to the model that this manager is attached to (your custom User model). This way, if you rename your User class, this code doesn't break.
        user = self.model(email=email, **extra_fields) # email + all other fields like password
        user.set_password(password) # hash_password
        user.save(using=self._db)
        return user

    def create_superuser(self, email, password=None, **extra_fields):
        extra_fields.setdefault('is_staff', True)
        extra_fields.setdefault('is_superuser', True)
        return self.create_user(email,password, **extra_fields)

class User(BaseModel, AbstractBaseUser, PermissionsMixin):
    class Role(models.TextChoices):
        EMPLOYEE = 'EMP', _('EMPLOYEE')
        ADMIN = 'ADM', _('ADMIN')
        FINANCE_OFFICER = 'FO', _('FINANCE OFFICER')
        CHIEF_FINANCE_OFFICER = 'CFO', _('Chief Finance Officer')

    class Status(models.TextChoices):
        ACTIVE = 'ACT', _('Active')
        ON_LEAVE = 'LEAVE', _('On Leave')
        INACTIVE = 'INACT', _('Inactive')

    email = models.EmailField(unique=True, verbose_name=_('Email'))
    first_name = models.CharField(max_length=150, blank=True, verbose_name=_('First name'))
    last_name = models.CharField(max_length=150, blank=True, verbose_name=_('Last name'))
    other_name = models.CharField(max_length=150, blank=True, null=True, verbose_name=_('Other name'))
    phone_number = models.CharField(max_length=20, blank=True, verbose_name=_('Phone Number'))
    national_id = models.CharField(max_length=150, blank=True, null=True, verbose_name=_('National Identity Number'))
    last_login = models.DateTimeField(blank=True, null=True)
    is_active = models.BooleanField(default=True)
    status = models.CharField(max_length=15,choices=Status, default=Status.ACTIVE)
    role = models.CharField(max_length=15,choices=Role, default=Role.EMPLOYEE)
    is_staff = models.BooleanField(default=True)
    avatar_url = models.CharField(max_length=500, blank=True, null=True)

    # default manager for this class
    objects = UserManager()
    USERNAME_FIELD = 'email'
    REQUIRED_FIELDS = ['']

    def __str__(self):
        return self.first_name+" "+self.last_name