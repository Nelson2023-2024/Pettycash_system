from django.db import models
from django.contrib.auth.models import (
    BaseUserManager,
    AbstractBaseUser,
    PermissionsMixin,
)
from base.models import BaseModel, GenericBaseModel, Status
from django.utils.translation import gettext_lazy as _
from department.models import Department


class Permission(GenericBaseModel):
    """
    A single action a user can perform.
    Assigned to roles — not directly to users.
    """

    code = models.CharField(
        max_length=150, unique=True, blank=True, null=True, verbose_name=_("Code")
    )

    class Meta:
        db_table = "permissions"
        verbose_name = _("Permission")
        verbose_name_plural = _("Permissions")

    def __str__(self):
        return self.code


class Role(GenericBaseModel):
    code = models.CharField(max_length=20, unique=True)
    permissions = models.ManyToManyField(
        Permission,
        related_name="roles",
        blank=True,
        null=True,
        verbose_name=_("Permissions"),
    )

    def __str__(self):
        return self.name

    class Meta:
        db_table = "role"
        verbose_name = _("Role")
        verbose_name_plural = _("Roles")
        ordering = ["-created_at"]


# Create your models here.
class UserManager(BaseUserManager):
    def create_user(self, email, password=None, **extra_fields):
        # validation error when we dont pass email later
        if not email:
            raise ValueError("Users must have an email address")
        email = self.normalize_email(
            email
        )  # Normalize the email address by lowercasing the domain part of it.

        # auto assign a status if not provided
        if "status" not in extra_fields:
            status, _ = Status.objects.get_or_create(
                code="ACT", defaults={"name": "Active", "description": "Active user"}
            )
            extra_fields["status"] = status

        # Auto-assign a default Role if not provided
        if "role" not in extra_fields:
            role, _ = Role.objects.get_or_create(
                code="EMP",
                defaults={"name": "Employee", "description": "Standard user"},
            )
            extra_fields["role"] = role

        # It refers to the model that this manager is attached to (your custom User model). This way, if you rename your User class, this code doesn't break.
        user = self.model(
            email=email, **extra_fields
        )  # email + all other fields like password
        user.set_password(password)  # hash_password
        user.save(using=self._db)
        return user

    def create_superuser(self, email, password=None, **extra_fields):
        extra_fields.setdefault("is_staff", True)
        extra_fields.setdefault("is_superuser", True)

        # Superusers get an ADMIN role
        if "role" not in extra_fields:
            role, _ = Role.objects.get_or_create(
                code="ADM", defaults={"name": "Admin", "description": "Administrator"}
            )
            extra_fields["role"] = role
        return self.create_user(email, password, **extra_fields)


class User(BaseModel, AbstractBaseUser, PermissionsMixin):
    email = models.EmailField(unique=True, verbose_name=_("Email"))
    first_name = models.CharField(
        max_length=150, blank=True, verbose_name=_("First name")
    )
    last_name = models.CharField(
        max_length=150, blank=True, verbose_name=_("Last name")
    )
    other_name = models.CharField(
        max_length=150, blank=True, null=True, verbose_name=_("Other name")
    )
    phone_number = models.CharField(
        max_length=20, blank=True, verbose_name=_("Phone Number")
    )
    national_id = models.CharField(
        max_length=150,
        blank=True,
        null=True,
        verbose_name=_("National Identity Number"),
    )
    avatar_url = models.ImageField(upload_to="avatars/", blank=True, null=True)

    last_login = models.DateTimeField(blank=True, null=True)

    is_active = models.BooleanField(default=True)
    is_staff = models.BooleanField(default=True)

    status = models.ForeignKey(
        Status,
        on_delete=models.PROTECT,
        related_name="users",
        verbose_name="Status",
    )

    department = models.ForeignKey(
        Department,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name="users",
        verbose_name=_("Department"),
    )

    role = models.ForeignKey(
        Role, on_delete=models.PROTECT, related_name="users", verbose_name="Role"
    )

    # OTP fields — logic lives in OTPService, not here
    otp_code = models.CharField(
        max_length=6, blank=True, null=True, verbose_name=_("OTP Code")
    )
    otp_expires_at = models.DateTimeField(
        blank=True, null=True, verbose_name=_("OTP Expires At")
    )

    # default manager for this class
    objects = UserManager()
    USERNAME_FIELD = "email"
    REQUIRED_FIELDS = []

    def __str__(self):
        return self.first_name + " " + self.last_name

    class Meta:
        db_table = "users"
        verbose_name = _("User")
        verbose_name_plural = _("Users")
        ordering = ["-created_at"]
