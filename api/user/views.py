from django.conf import settings
from django.db import transaction
from drf_spectacular.utils import extend_schema
from itsdangerous.exc import BadSignature, BadTimeSignature, SignatureExpired
from rest_framework.permissions import AllowAny, IsAuthenticated
from rest_framework.response import Response
from rest_framework.views import APIView
from rest_framework_jwt.settings import api_settings
from rest_framework_jwt.views import (
    ObtainJSONWebTokenView as RegularObtainJSONWebToken,
    RefreshJSONWebTokenView as RegularRefreshJSONWebToken,
    VerifyJSONWebTokenView as RegularVerifyJSONWebToken,
)

from api.errors import (
    ERROR_ALREADY_EXISTS,
    BAD_TOKEN_SIGNATURE,
    ERROR_DISABLED_SIGNUP,
    ERROR_INVALID_OLD_PASSWORD,
    EXPIRED_TOKEN_SIGNATURE,
    ERROR_USER_NOT_FOUND,
    ERROR_HOSTNAME_IS_NOT_ALLOWED, PIN_NOT_EXISTS, PIN_EXPIRED
)
from api.schemas import create_user_response_schema, get_error_schema, authenticate_user_schema
from api.user.serializers import (
    RegisterSerializer,
    UserSerializer,
    ChangePasswordBodyValidationSerializer,
    ResetPasswordBodyValidationSerializer,
    SendResetPasswordEmailBodyValidationSerializer,
    NormalizedEmailWebTokenSerializer,
    GetUserSerializer,
    ForgotPasswordBodyValidationSerializer,
    GetUserChatSerializer
)
from core.decorators import map_exceptions, validate_body
from core.exceptions import (
    UserAlreadyExist,
    DisabledSignupError,
    InvalidPassword,
    UserNotFound,
    BaseURLHostnameNotAllowed, PinExpired, PinNotExists
)
from core.jwt import user_data_registry
from core.models import UserPin, User, UserType
from core.users.handler import UserHandler, OptimizeUserHandler
from utils.base_views import PaginationApiView

jwt_payload_handler = api_settings.JWT_PAYLOAD_HANDLER
jwt_encode_handler = api_settings.JWT_ENCODE_HANDLER


class SearchUserChatApiView(PaginationApiView):
    permission_classes = (IsAuthenticated,)

    def get(self, request):
        data_param = request.GET
        name_search_user = data_param.get('name', '')

        list_user = OptimizeUserHandler().get_list_user(
            data_filter_name=name_search_user,
            ignore_role_admin=True
        )
        page_info, paginated_data = self.get_paginated(list_user)

        serializer = GetUserChatSerializer(paginated_data, many=True)
        payload = []
        if len(serializer.data):
            for item in serializer.data:
                payload.append({
                    **item['info']
                })
        response = {
            'payload': payload,
            'page_info': page_info
        }
        return Response(response, status=200)


class ListUserApiView(PaginationApiView):
    permission_classes = (AllowAny,)

    def get(self, request):
        data_param = request.GET
        name_search_user = data_param.get('name', '')

        filter_role = data_param.get('role', '')

        list_user = OptimizeUserHandler().get_list_user(
            data_filter_name=name_search_user,
            filter_role=filter_role
        )
        # response
        page_info, paginated_data = self.get_paginated(list_user)
        serializer = GetUserSerializer(paginated_data, many=True)
        response = {
            'payload': serializer.data,
            'page_info': page_info
        }
        return Response(response, status=200)

    def post(self, request):
        data = request.data
        new_user = OptimizeUserHandler().create_new_user(data)
        serializer = GetUserSerializer(new_user)
        response = {
            'payload': serializer.data
        }
        return Response(response, status=200)


class DetailUserApiView(APIView):
    permission_classes = (IsAuthenticated,)

    def get(self, request, user_id):
        user = OptimizeUserHandler().get_detail_user(user_id)
        serializer = GetUserSerializer(user)
        response = {
            "payload": serializer.data
        }
        return Response(response, status=200)

    def put(self, request, user_id):
        data = request.data
        try:
            OptimizeUserHandler().update_user(user_id=user_id, data=data)
            return Response(
                {
                    'payload': None
                },
                status=200
            )
        except:
            return Response(
                {
                    'payload': None,
                    'error': 'Check data',
                },
                status=400
            )

    def delete(self, request, user_id):
        try:
            OptimizeUserHandler().delete_user(user_id)
            return Response(
                {
                    'payload': None
                },
                status=204
            )
        except:
            return Response(
                {
                    'payload': None,
                    'error': 'Something went wrong!',
                },
                status=400
            )


class UserView(APIView):
    permission_classes = (IsAuthenticated,)

    def get(self, request, ):
        """update a new user."""
        user = request.user

        response = {"payload": GetUserSerializer(user).data}
        return Response(response, status=200)

    @extend_schema(
        tags=["User"],
        request=RegisterSerializer,
        operation_id="create_user",
        description=(
                "Creates a new user based on the provided values. If desired an "
                "authentication token can be generated right away. After creating an "
                "account the initial group containing a database is created."
        ),
        responses={
            200: create_user_response_schema,
            400: get_error_schema(
                [
                    "ERROR_ALREADY_EXISTS",
                    "ERROR_GROUP_INVITATION_DOES_NOT_EXIST"
                    "ERROR_REQUEST_BODY_VALIDATION",
                    "BAD_TOKEN_SIGNATURE",
                ]
            ),
            404: get_error_schema(["ERROR_GROUP_INVITATION_DOES_NOT_EXIST"]),
        },
        auth=[None],
    )
    @transaction.atomic
    @map_exceptions(
        {
            UserAlreadyExist: ERROR_ALREADY_EXISTS,
            BadSignature: BAD_TOKEN_SIGNATURE,
            DisabledSignupError: ERROR_DISABLED_SIGNUP,
        }
    )
    @validate_body(RegisterSerializer)
    def post(self, request, data):
        """Registers a new user."""

        user = UserHandler().create_user(
            first_name=data["first_name"],
            last_name=data["last_name"],
            email=data["email"],
            password=data["password"],
        )

        response = {"user": UserSerializer(user).data}

        if data["authenticate"]:
            payload = jwt_payload_handler(user)
            token = jwt_encode_handler(payload)
            response.update(token=token)
            response.update(**user_data_registry.get_all_user_data(user, request))

        return Response(response)

    def put(self, request):
        """update a new user."""
        data = request.data
        user = UserHandler().update_user_multi_field(data)

        response = {"payload": GetUserSerializer(user).data}
        return Response(response, status=200)


class ChangePasswordView(APIView):
    permission_classes = (IsAuthenticated,)

    @extend_schema(
        tags=["User"],
        request=ChangePasswordBodyValidationSerializer,
        operation_id="change_password",
        description=(
                "Changes the password of an authenticated user, but only if the old "
                "password matches."
        ),
        responses={
            204: None,
            400: get_error_schema(
                [
                    "ERROR_INVALID_OLD_PASSWORD",
                    "ERROR_REQUEST_BODY_VALIDATION",
                ]
            ),
        },
    )
    @transaction.atomic
    @map_exceptions(
        {
            InvalidPassword: ERROR_INVALID_OLD_PASSWORD,
        }
    )
    @validate_body(ChangePasswordBodyValidationSerializer)
    def post(self, request, data):
        """Changes the authenticated user's password if the old password is correct."""

        handler = UserHandler()
        handler.change_password(
            request.user, data["old_password"], data["new_password"]
        )

        return Response("", status=204)


class ForgotPasswordView(APIView):
    permission_classes = (AllowAny,)
    serializer_class = ForgotPasswordBodyValidationSerializer

    @map_exceptions(
        {
            InvalidPassword: ERROR_INVALID_OLD_PASSWORD,
            PinExpired: PIN_EXPIRED,
            PinNotExists: PIN_NOT_EXISTS,
            UserNotFound: ERROR_USER_NOT_FOUND,
        }
    )
    # @validate_body(ForgotPasswordBodyValidationSerializer)
    def post(self, request):
        """Changes the user's password if forgot."""
        data = request.data
        serializer = self.serializer_class(data=data)
        if serializer.is_valid(raise_exception=True):
            handler = UserHandler()
            handler.create_new_password(
                serializer.data.get('email'), serializer.data.get('new_password')
            )
            UserPin.objects.get(
                code=serializer.data.get("pin", ""),
                device_token=serializer.data.get("token", "")
            ).delete()

            return Response({"payload": None}, status=200)


class ResetPasswordView(APIView):
    permission_classes = (AllowAny,)

    @extend_schema(
        tags=["User"],
        request=ResetPasswordBodyValidationSerializer,
        operation_id="reset_password",
        description=(
                "Changes the password of a user if the reset token is valid. The "
                "**send_password_reset_email** endpoint sends an email to the user "
                "containing the token. That token can be used to change the password "
                "here without providing the old password."
        ),
        responses={
            204: None,
            400: get_error_schema(
                [
                    "BAD_TOKEN_SIGNATURE",
                    "EXPIRED_TOKEN_SIGNATURE",
                    "ERROR_USER_NOT_FOUND",
                    "ERROR_REQUEST_BODY_VALIDATION",
                ]
            ),
        },
        auth=[None],
    )
    @transaction.atomic
    @map_exceptions(
        {
            BadSignature: BAD_TOKEN_SIGNATURE,
            BadTimeSignature: BAD_TOKEN_SIGNATURE,
            SignatureExpired: EXPIRED_TOKEN_SIGNATURE,
            UserNotFound: ERROR_USER_NOT_FOUND,
        }
    )
    @validate_body(ResetPasswordBodyValidationSerializer)
    def post(self, request, data):
        """Changes users password if the provided token is valid."""

        handler = UserHandler()
        handler.reset_password(data["token"], data["password"])

        return Response("", status=204)


class SendResetPasswordEmailView(APIView):
    permission_classes = (AllowAny,)

    @extend_schema(
        tags=["User"],
        request=SendResetPasswordEmailBodyValidationSerializer,
        operation_id="send_password_reset_email",
        description=(
                "Sends an email containing the password reset link to the email address "
                "of the user. This will only be done if a user is found with the given "
                "email address. The endpoint will not fail if the email address is not "
                "found. The link is going to the valid for {valid} hours.".format(
                    valid=int(settings.RESET_PASSWORD_TOKEN_MAX_AGE / 60 / 60)
                )
        ),
        responses={
            204: None,
            400: get_error_schema(
                ["ERROR_REQUEST_BODY_VALIDATION", "ERROR_HOSTNAME_IS_NOT_ALLOWED"]
            ),
        },
        auth=[None],
    )
    @transaction.atomic
    @validate_body(SendResetPasswordEmailBodyValidationSerializer)
    @map_exceptions({BaseURLHostnameNotAllowed: ERROR_HOSTNAME_IS_NOT_ALLOWED})
    def post(self, request, data):
        """
        If the email is found, an email containing the password reset link is send to
        the user.
        """

        handler = UserHandler()

        try:
            user = handler.get_user(email=data["email"])
            handler.send_reset_password_email(user, data["base_url"])
        except UserNotFound:
            pass

        return Response("", status=204)


class VerifyJSONWebToken(RegularVerifyJSONWebToken):
    @extend_schema(
        tags=["User"],
        operation_id="token_verify",
        description="Verifies if the token is still valid.",
        responses={
            200: authenticate_user_schema,
            400: {"description": "The token is invalid or expired."},
        },
        auth=[None],
    )
    def post(self, *args, **kwargs):
        return super().post(*args, **kwargs)


class RefreshJSONWebToken(RegularRefreshJSONWebToken):
    @extend_schema(
        tags=["User"],
        operation_id="token_refresh",
        description=(
                "Refreshes an existing JWT token. If the the token is valid, a new "
                "token will be included in the response. It will be valid for {valid} "
                "minutes.".format(
                    valid=int(settings.JWT_AUTH["JWT_EXPIRATION_DELTA"].seconds / 60)
                )
        ),
        responses={
            200: authenticate_user_schema,
            400: {"description": "The token is invalid or expired."},
        },
        auth=[None],
    )
    def post(self, *args, **kwargs):
        return super().post(*args, **kwargs)


class ObtainJSONWebToken(RegularObtainJSONWebToken):
    """
    A slightly modified version of the ObtainJSONWebToken that uses an email as
    username and normalizes that email address using the normalize_email_address
    utility function.
    """

    serializer_class = NormalizedEmailWebTokenSerializer

    @extend_schema(
        tags=["User"],
        operation_id="token_auth",
        description=(
                "Authenticates an existing user based on their username, which is their "
                "email address, and their password. If successful a JWT token will be "
                "generated that can be used to authorize for other endpoints that require "
                "authorization. The token will be valid for {valid} minutes, so it has to "
                "be refreshed using the **token_refresh** endpoint before that "
                "time.".format(
                    valid=int(settings.JWT_AUTH["JWT_EXPIRATION_DELTA"].seconds / 60)
                )
        ),
        responses={
            200: authenticate_user_schema,
            400: {
                "description": "A user with the provided username and password is "
                               "not found."
            },
        },
        auth=[None],
    )
    def post(self, *args, **kwargs):
        return super().post(*args, **kwargs)
