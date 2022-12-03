# from django.contrib.auth.hashers import make_password, check_password
import secrets
from datetime import datetime
from random import randint

from django.conf import settings
from django.contrib.auth.base_user import (
    AbstractBaseUser,
    BaseUserManager,
)
from django.db import models
from rest_framework_jwt.settings import api_settings
from django.contrib.auth.models import PermissionsMixin

from core.exceptions import UserNotFound
from utils.validators import validate_phone_number
from django.utils.translation import gettext_lazy as _

jwt_payload_handler = api_settings.JWT_PAYLOAD_HANDLER
jwt_encode_handler = api_settings.JWT_ENCODE_HANDLER


# Create your models here.

# class Settings(models.Model):
#     """
#     The settings model represents the application wide settings that only admins can
#     change. This table can only contain a single row.
#     """
#
#     instance_id = models.SlugField(default=secrets.token_urlsafe)
#     allow_new_signups = models.BooleanField(
#         default=True,
#         help_text="Indicates whether new users can create a new account when signing "
#                   "up.",
#     )


class UserType(models.TextChoices):
    STUDENT = 'STUDENT'
    TEACHER = 'TEACHER'
    PARENT = 'PARENT'
    ADMIN = 'ADMIN'


class TimeStampMixin(models.Model):
    """
    An abstract base class model that provides self-updating
    ``created`` and ``modified`` fields.
    """
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        abstract = True


class UserManager(BaseUserManager):
    def create_user(self, email, username, password=None):
        user = self.model(
            email=email,
            username=username,
        )
        # you can use `make_password` instead

        user.set_password(password)
        user.save(using=self._db)
        return user

    def create_superuser(self, email, username, password):
        user = self.create_user(
            email=email,
            username=username,
            password=password,
        )
        user.is_superuser = True
        user.is_staff = True
        user.save(using=self._db)
        return user


class User(AbstractBaseUser, TimeStampMixin, PermissionsMixin):
    first_name = models.CharField(max_length=255, blank=True, null=True)
    last_name = models.CharField(max_length=255, blank=True, null=True)
    username = models.CharField(max_length=255, blank=True, null=True, unique=True)
    email = models.EmailField(max_length=200, blank=True, null=True, unique=True)
    phone = models.CharField(max_length=255, blank=True, null=True, validators=[validate_phone_number])
    role = models.CharField(choices=UserType.choices, max_length=50, blank=True, null=True)
    avatar_url = models.CharField(max_length=255, blank=True, null=True)
    address = models.CharField(max_length=255, blank=True, null=True)
    date_of_birth = models.DateTimeField(blank=True, null=True)
    deleted_at = models.DateTimeField(blank=True, null=True)
    last_accessed_at = models.DateTimeField(blank=True, null=True)
    is_superuser = models.BooleanField(default=False)
    is_staff = models.BooleanField(
        _("staff status"),
        default=False,
        help_text=_("Designates whether the user can log into this admin site."),
    )

    USERNAME_FIELD = 'username'
    REQUIRED_FIELDS = ['email']

    objects = UserManager()

    class Meta:
        db_table = "user"

    # @staticmethod
    # def search_customer(merchant_id, store_id, term):
    #     user = User.objects.filter(
    #         store_user_user__store_id=store_id,
    #         store_user_user__role__name=RoleName.CUSTOMER,
    #     )
    #     if term:
    #         user = user.filter(
    #             Q(family_name__icontains=term) |
    #             Q(given_name__icontains=term) |
    #             Q(email__icontains=term)
    #         )
    #     return user

    @staticmethod
    def get_user_by_phone(phone):
        try:
            return User.objects.get(phone=phone)
        except User.DoesNotExist:
            raise UserNotFound('The user does not exist')


class UserPin(TimeStampMixin):
    code = models.IntegerField()
    pin_expired = models.DateTimeField()
    device_token = models.TextField(max_length=300, blank=True, null=True)

    user = models.ForeignKey(User, on_delete=models.SET_NULL, null=True, blank=True, related_name="user")

    class Meta:
        db_table = "user_pin"

    def generate_pin(self, user):
        self.code = randint(100000, 999999)
        pin_expiration_delta = settings.PIN_EXPIRATION_DELTA
        self.pin_expired = datetime.utcnow() + pin_expiration_delta
        if user.id is not None:
            self.user = user
        payload = jwt_payload_handler(user)
        token = jwt_encode_handler(payload)
        self.device_token = token
        self.save()
        return self

    def generate_pin_sign_up(self):
        self.code = randint(100000, 999999)
        pin_expiration_delta = settings.PIN_EXPIRATION_DELTA
        self.pin_expired = datetime.utcnow() + pin_expiration_delta
        self.device_token = secrets.token_urlsafe(180)
        self.save()
        return self

# class UserLogEntry(models.Model):
#     actor = models.ForeignKey(User, on_delete=models.CASCADE)
#     action = models.CharField(max_length=20, choices=(("SIGNED_IN", "Signed in"),))
#     timestamp = models.DateTimeField(auto_now_add=True)
#
#     class Meta:
#         get_latest_by = "timestamp"
#         ordering = ["-timestamp"]


# class Permission(Group, TimeStampMixin):
#     permission_name = models.CharField(max_length=255, blank=True, null=True, help_text="Permission name")
#     description = models.TextField(max_length=255, blank=True, null=True)
#     category = models.IntegerField(choices=PermissionStatus.choices, default=None, null=True, blank=True)
#     deleted_at = models.DateTimeField(blank=True, null=True)
#
#     parent = models.ForeignKey(
#         "self",
#         on_delete=models.CASCADE,
#         default=None,
#         null=True,
#         blank=True,
#         related_name="permission_category"
#     )
#     objects = models.Manager()
#
#     class Meta:
#         verbose_name = "Permission"
#         verbose_name_plural = "Persmissions"
#
#     def __unicode__(self):
#         return self.name
#
#     @staticmethod
#     def get_permission_of_super_admin():
#         return map(lambda perm: perm.get("permission_name"), Permission.objects.all())


# class Role(TimeStampMixin):
#     name = models.CharField(max_length=255, blank=True, null=True)
#     deleted_at = models.DateTimeField(blank=True, null=True)
#
#     permissions = models.ManyToManyField(Permission, related_name="role_permissions")
#
#     class Meta:
#         db_table = "role"


# class UserRole(TimeStampMixin):
#     role = models.ForeignKey(Role, on_delete=models.SET_NULL, null=True, related_name="user_role_role")
#     user = models.ForeignKey(User, on_delete=models.SET_NULL, null=True, related_name="user_role_user")
#     is_active = models.BooleanField(default=False)
#
#     class Meta:
#         db_table = "user_role"
