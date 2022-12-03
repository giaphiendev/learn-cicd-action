import logging
from datetime import datetime
from urllib.parse import (
    urlparse,
    urljoin,
)
from itsdangerous import URLSafeTimedSerializer

from django.core.mail import send_mail
from django.template.loader import render_to_string
from django.conf import settings
from django.core.exceptions import ValidationError
from django.contrib.auth import get_user_model
from django.contrib.auth.password_validation import validate_password
from django.db.models import Q
from django.utils import translation
from rest_framework_simplejwt.tokens import (
    RefreshToken,
    TokenError,
)

from custom_service.models.ModelTechwiz import Student
from .errors import ERROR_INVALID_TOKEN
from core.utils import encode_base_64
from core.constants import RoleName
from core.handler import CoreHandler
from core.exceptions import (
    BaseURLHostnameNotAllowed,
)
from core.models import (
    UserPin, UserType,
    # UserRole,
)

from core.exceptions import (
    PinExpired,
    PinNotExists,
    UserAlreadyExist,
    UserNotFound,
    PasswordDoesNotMatchValidation,
    InvalidPassword,
    DisabledSignupError,
)
from .emails import ResetPasswordEmail
from .utils import normalize_email_address
from rest_framework_jwt.settings import api_settings

logger = logging.getLogger('django')

User = get_user_model()

jwt_payload_handler = api_settings.JWT_PAYLOAD_HANDLER
jwt_encode_handler = api_settings.JWT_ENCODE_HANDLER
jwt_decode_handler = api_settings.JWT_DECODE_HANDLER


class OptimizeUserHandler:
    def get_list_user(self, data_filter_name=None, ignore_role_admin=False, filter_role=None):
        """
        @param data_filter_name: str
        @return: list_user: User
        """

        if ignore_role_admin:
            list_user = User.objects.filter(
                Q(role__in=[UserType.STUDENT, UserType.PARENT, UserType.TEACHER])
            )
        else:
            if filter_role == 'parent':
                list_user = User.objects.filter(role=UserType.PARENT)
            elif filter_role == 'teacher':
                list_user = User.objects.filter(role=UserType.TEACHER)
            elif filter_role == 'student':
                list_user = User.objects.filter(role=UserType.STUDENT)
            else:
                list_user = User.objects.all()

        if data_filter_name:
            return list_user.filter(
                Q(first_name__istartswith=data_filter_name) |
                Q(last_name__istartswith=data_filter_name) |
                Q(email__icontains=data_filter_name)
            ).union(
                list_user.filter(
                    Q(first_name__icontains=data_filter_name) |
                    Q(last_name__icontains=data_filter_name)
                )
            )
        return list_user

    def get_detail_user(self, user_id):
        return User.objects.get(pk=user_id)

    def create_new_user(self, data, data_student=None, create_student=False):
        """
        @param
        data: {
            first_name: ''
            last_name: ''
            email: 'abc@yopmail.com'
            phone: 0987632333
            role: UserType
            address: ''
            date_of_birth: ''
        }
        data_student: {
            parent: User,
            my_class: MyClass
        }
        @return: new_user: User
        """
        email = normalize_email_address(data.get('email'))
        data['email'] = email
        data['username'] = email.split('@')[0]

        if User.objects.filter(Q(email=email) | Q(username=email)).exists():
            raise UserAlreadyExist(f"A user with username {email} already exists.")
        new_user = User.objects.create(**data)

        if create_student and data_student:
            Student.objects.create(user=new_user, **data_student)
        return new_user

    def update_user(self, user_id, data):
        """
        @param
        user_id: int
        data: {
            first_name: ''
            last_name: ''
            email: 'abc@yopmail.com'
            phone: 0987632333
            role: UserType
            address: ''
            date_of_birth: ''
        }
        """
        User.objects.filter(pk=user_id).update(**data)

    def update_student(self, student_id, data_student):
        """
        @param student_id: int
        @param data_student: {
            parent: User,
            my_class: MyClass
        }
        """
        Student.objects.filter(pk=student_id).update(**data_student)

    def delete_user(self, user_id):
        user = User.objects.filter(pk=user_id).first()
        user.delete()


class UserHandler:
    def get_user(self, user_id=None, email=None):
        """
        Finds and returns a single user instance based on the provided parameters.

        :param user_id: The user id of the user.
        :type user_id: int
        :param email: The username, which is their email address, of the user.
        :type email: str
        :raises ValueError: When neither a `user_id` or `email` has been provided.
        :raises UserNotFound: When the user with the provided parameters has not been
            found.
        :return: The requested user.
        :rtype: User
        """

        if not user_id and not email:
            raise ValueError("Either a user id or email must be provided.")

        query = User.objects.all()

        if user_id:
            query = query.filter(id=user_id)

        if email:
            email = normalize_email_address(email)
            query = query.filter(username=email)

        try:
            return query.get()
        except User.DoesNotExist:
            raise UserNotFound("The user with the provided parameters is not found.")

    def create_user(
            self,
            first_name,
            last_name,
            email,
            password,
    ):
        """
        Creates a new user with the provided information and creates a new group and
        application for him. If the optional group invitation is provided then the user
        joins that group without creating a new one.

        :param first_name: The first_name of the new user.
        :type first_name: str
        :param last_name: The last_name of the new user.
        :type last_name: str
        :param email: The e-mail address of the user, this is also the username.
        :type email: str
        :param password: The password of the user.
        :type password: str
        :param language: The language selected by the user.
        :type language: str
        :param group_invitation_token: If provided and valid, the invitation will be
            accepted and and initial group will not be created.
        :type group_invitation_token: str
        :param template: If provided, that template will be installed into the newly
            created group.
        :type template: Template
        :raises: UserAlreadyExist: When a user with the provided username (email)
            already exists.
        :raises GroupInvitationEmailMismatch: If the group invitation email does not
            match the one of the user.
        :raises SignupDisabledError: If signing up is disabled.
        :raises PasswordDoesNotMatchValidation: When a provided password does not match
            password validation.
        :return: The user object.
        :rtype: User
        """

        core_handler = CoreHandler()

        if not core_handler.get_settings().allow_new_signups:
            raise DisabledSignupError("Sign up is disabled.")

        email = normalize_email_address(email)

        if User.objects.filter(Q(email=email) | Q(username=email)).exists():
            raise UserAlreadyExist(f"A user with username {email} already exists.")

        user = User(first_name=first_name, last_name=last_name, email=email, username=email)

        try:
            validate_password(password, user)
        except ValidationError as e:
            raise PasswordDoesNotMatchValidation(e.messages)

        user.set_password(password)

        if not User.objects.exists():
            # This is the first ever user created in this oneclick instance and
            # therefore the administrator user, lets give them staff rights so they
            # can set oneclick wide settings.
            user.is_staff = True

        user.save()

        return user

    def update_user_multi_field(self, data):
        """
        Update user modifiable properties
        args:
            data: {id: 1, first_name: '', last_name: ''}
        return:
            user
        """
        try:
            User.objects.filter(id=data.get('id')).update(**data)
            return User.objects.get(pk=data.get("id"))
        except User.DoesNotExist:
            raise UserNotFound('User not found')

    def update_user(self, user, first_name=None, language=None):
        """
        Update user modifiable properties

        :param user: The user instance to update.
        :type user: User
        :param language: The language selected by the user.
        :type language: str
        :return: The user object.
        :rtype: User
        """

        if first_name is not None:
            user.first_name = first_name
            user.save()

        if language is not None:
            user.profile.language = language
            user.profile.save()

        return user

    def get_reset_password_signer(self):
        """
        Instantiates the password reset serializer that can dump and load values.

        :return: The itsdangerous serializer.
        :rtype: URLSafeTimedSerializer
        """

        return URLSafeTimedSerializer(settings.SECRET_KEY, "user-reset-password")

    def send_reset_password_email(self, user, base_url):
        """
        Sends an email containing a password reset url to the user.

        :param user: The user instance.
        :type user: User
        :param base_url: The base url of the frontend, where the user can reset his
            password. The reset token is appended to the URL (base_url + '/TOKEN').
            Only the PUBLIC_WEB_FRONTEND_HOSTNAME is allowed as domain name.
        :type base_url: str
        """

        parsed_base_url = urlparse(base_url)
        if parsed_base_url.hostname != settings.PUBLIC_WEB_FRONTEND_HOSTNAME:
            raise BaseURLHostnameNotAllowed(
                f"The hostname {parsed_base_url.netloc} is not allowed."
            )

        signer = self.get_reset_password_signer()
        signed_user_id = signer.dumps(user.id)

        if not base_url.endswith("/"):
            base_url += "/"

        reset_url = urljoin(base_url, signed_user_id)

        with translation.override(user.profile.language):
            email = ResetPasswordEmail(user, reset_url, to=[user.email])
            email.send()

    def reset_password(self, token, password):
        """
        Changes the password of a user if the provided token is valid.

        :param token: The signed token that was send to the user.
        :type token: str
        :param password: The new password of the user.
        :type password: str
        :raises BadSignature: When the provided token has a bad signature.
        :raises SignatureExpired: When the provided token's signature has expired.
        :raises UserNotFound: When a user related to the provided token has not been
            found.
        :raises PasswordDoesNotMatchValidation: When a provided password does not match
            password validation.
        :return: The updated user instance.
        :rtype: User
        """

        signer = self.get_reset_password_signer()
        user_id = signer.loads(token, max_age=settings.RESET_PASSWORD_TOKEN_MAX_AGE)

        user = self.get_user(user_id=user_id)

        try:
            validate_password(password, user)
        except ValidationError as e:
            raise PasswordDoesNotMatchValidation(e.messages)

        user.set_password(password)
        user.save()

        return user

    def create_new_password(self, email, new_password):
        """
        create new password
        """
        try:
            user = User.objects.get(email=email)
            validate_password(new_password, user)

            user.set_password(new_password)
            user.save()
        except User.DoesNotExist:
            raise UserNotFound('User not found')
        except ValidationError as e:
            raise PasswordDoesNotMatchValidation(e.messages)

    def change_password(self, user, old_password, new_password):
        """
        Changes the password of the provided user if the old password matches the
        existing one.

        :param user: The user for which the password needs to be changed.
        :type user: User
        :param old_password: The old password of the user. This must match with the
            existing password else the InvalidPassword exception is raised.
        :type old_password: str
        :param new_password: The new password of the user. After changing the user
            can only authenticate with this password.
        :type new_password: str
        :raises InvalidPassword: When the provided old password is incorrect.
        :raises PasswordDoesNotMatchValidation: When a provided password does not match
            password validation.
        :return: The changed user instance.
        :rtype: User
        """

        if not user.check_password(old_password):
            raise InvalidPassword("The provided old password is incorrect.")

        try:
            validate_password(new_password, user)
        except ValidationError as e:
            raise PasswordDoesNotMatchValidation(e.messages)

        user.set_password(new_password)
        user.save()

        return user

    def get_user_by_pin(self, data):
        """
        Check user and pin for login function
        """
        try:
            pin = UserPin.objects.get(
                code=data.get("pin", ""),
                device_token=data.get("token", "")
            )
            if pin.pin_expired < datetime.now():
                raise PinExpired('Pin expired')
            user = User.objects.get(
                email=data.get("email", ""),
                # user__code=data.get("pin", ""),
                # user__pin_expired__gte=datetime.utcnow(),
                # user__device_token=data.get("token", ""),
            )
            user.last_accessed_at = datetime.utcnow()
            user.save()
        except User.DoesNotExist:
            raise UserNotFound('User Not Found')
        except UserPin.DoesNotExist:
            raise PinNotExists('Pin not exists')
        UserPin.objects.get(code=data.get("pin", "")).delete()
        return user

    def get_user_by_password(self, data):
        """
        Check user and password for login function

        :param data: {
            email: '',
            password: ''
        }

        : return user
        """
        try:
            user = User.objects.get(
                email=data.get("email", "")
            )
            if not user.check_password(data.get("password", "")):
                raise InvalidPassword("The provided password is incorrect.")
            user.last_accessed_at = datetime.utcnow()
            user.save()
        except User.DoesNotExist:
            raise UserNotFound('User Not Found')
        return user

    def get_pin(self, data, delete_pin=True):
        """
        Check user and pin for login function
        """
        try:
            pin = UserPin.objects.get(code=data.get("pin", ""),
                                      device_token=data.get("token", ""))

            if pin.pin_expired < datetime.now():
                raise PinExpired('Pin expired')
        except UserPin.DoesNotExist:
            raise PinNotExists('Pin not exists')
        # if delete_pin:
        #     UserPin.objects.get(code=data.get("pin", ""), device_token=data.get("token", "")).delete()
        return pin

    def get_super_user_by_email(self, email):
        """
        Check user and pin for login
        """
        try:
            user = User.objects.get(
                email=email,
                is_superuser=True
            )
        except User.DoesNotExist:
            raise UserNotFound("The email is non-existent")
        return user

    def logout_customer(self, token):
        """
        Add refresh token to blacklist
        """
        try:
            RefreshToken(token).blacklist()
        except TokenError:
            raise ERROR_INVALID_TOKEN("The token is invalid")

    # def delete_user(self, user_id):
    #     try:
    #         manage_role = [
    #             RoleName.SUPER_ADMIN,
    #             RoleName.STAFF,
    #             RoleName.ADMIN,
    #             RoleName.DEVELOP,
    #         ]
    #         user = UserRole.objects.get(
    #             user__id=user_id,
    #             role__name__in=manage_role,
    #             deleted_at=None,
    #         )
    #         user.deleted_at = datetime.utcnow()
    #         user.save()
    #     except UserRole.DoesNotExist:
    #         raise UserNotFound("The user is not found.")

    def send_mail(self, email):
        template_mail_invite = "mails/master_invite.html"
        encode_email = encode_base_64(email)
        invitation_url = f'{settings.MASTER_ONE_CLICK_URL}/api/master/account/invite/validate?email={encode_email}'
        logo_url = f'https://{settings.AWS_S3_CUSTOM_DOMAIN}/logo_recustomer.png'
        context = {
            "invitation_url": invitation_url,
            "logo_url": logo_url,
            "privary_policy_url": settings.PRIVACY_POLICY_URL,
        }
        content = render_to_string(template_mail_invite, context)
        send_mail(
            subject="Invite",
            message=f"{settings.URL_MERCHANT}/set-pw?token=",
            html_message=content,
            from_email=settings.FROM_EMAIL,
            recipient_list=[email],
            fail_silently=False,
        )
