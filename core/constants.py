from django.db import models


class ResultStatus:
    SUCCESS = "success"
    FAILURE = "failure"


class RoleName:
    SUPER_ADMIN = "super_admin"
    ADMIN = "admin"
    STAFF = "staff"
    DEVELOP = "develop"
    CUSTOMER = "customer"


class PermissionStatus(models.IntegerChoices):
    SUPER = 1
    GENERAL = 2
    MANAGEMENT = 3
    DEVELOPER = 4
