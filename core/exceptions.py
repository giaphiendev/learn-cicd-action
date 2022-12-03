from rest_framework.exceptions import APIException


class UserNotFound(Exception):
    """Raised when a user with given parameters is not found."""


class RoleNotFound(Exception):
    """Raised when a role with given parameters is not found."""


class InstanceTypeDoesNotExist(Exception):
    """
    Raised when a requested instance model instance isn't registered in the registry.
    """

    def __init__(self, type_name, *args, **kwargs):
        self.type_name = type_name
        super().__init__(*args, **kwargs)


class InstanceTypeAlreadyRegistered(Exception):
    """
    Raised when the instance model instance is already registered in the registry.
    """


class RequestBodyValidationException(APIException):
    def __init__(self, detail=None, code=None):
        super().__init__(
            {
                "error": "ERROR_REQUEST_BODY_VALIDATION",
                "detail": detail
            },
            code=code
        )
        self.status_code = 400


class QueryParameterValidationException(APIException):
    def __init__(self, detail=None, code=None):
        super().__init__(
            {"error": "ERROR_QUERY_PARAMETER_VALIDATION", "detail": detail}, code=code
        )
        self.status_code = 400


class IsNotAdminError(Exception):
    """
    Raised when the user tries to perform an action that is not allowed because he
    does not have admin permissions.
    """


class BaseURLHostnameNotAllowed(Exception):
    """
    Raised when the provided base url is not allowed when requesting a password
    reset email.
    """


class PinExpired(Exception):
    """Raised when pin expired."""


class PinNotExists(Exception):
    """Raised when pin not exists."""


class UserAlreadyExist(Exception):
    """Raised when a user could not be created because the email already exists."""


class PasswordDoesNotMatchValidation(Exception):
    """Raised when the provided password does not match validation."""


class InvalidPassword(Exception):
    """Raised when the provided password is incorrect."""


class DisabledSignupError(Exception):
    """
    Raised when a user account is created when the new signup setting is disabled.
    """


class ApplicationTypeAlreadyRegistered(InstanceTypeAlreadyRegistered):
    pass


class ApplicationTypeDoesNotExist(InstanceTypeDoesNotExist):
    pass


class InvalidPin(Exception):
    """
    Raised when a pin is expired or wrong
    """
