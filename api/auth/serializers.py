from django.db import IntegrityError
from rest_framework import serializers
from rest_framework_simplejwt.serializers import TokenObtainPairSerializer

from api.errors import (
    ERROR_INVALID_PIN,
    ERROR_USER_NOT_FOUND,
    PIN_EXPIRED,
    PIN_NOT_EXISTS, ERROR_INVALID_PASSWORD
)
from core.decorators import map_exceptions
from core.exceptions import (
    InvalidPin,
    UserNotFound,
    PinNotExists,
    PinExpired, InvalidPassword
)
from core.models import User, UserType
from core.users.handler import UserHandler
from custom_service.models.ModelTechwiz import Student
from utils import error
from utils.logger import logger_raise_warn_exception


class GetAllFieldUserSerializer(serializers.ModelSerializer):
    class Meta:
        model = User
        fields = "__all__"
        extra_kwargs = {
            "password": {"write_only": True},
            "last_accessed_at": {"write_only": True},
            "is_superuser": {"write_only": True},
            "is_staff": {"write_only": True},
            "groups": {"write_only": True},
            "user_permissions": {"write_only": True},
        }

    def to_representation(self, instance):
        data = {
            "id": instance.id,
            "last_login": instance.last_login,
            "first_name": instance.first_name,
            "last_name": instance.last_name,
            "username": instance.username,
            "email": instance.email,
            "phone": instance.phone,
            "role": instance.role,
            "avatar_url": instance.avatar_url,
            "address": instance.address,
            "date_of_birth": instance.date_of_birth,
        }

        if instance.role == UserType.STUDENT:
            student = Student.objects.filter(user_id=instance.id).select_related('my_class').select_related(
                'parent').first()
            my_class = student.my_class
            parent = student.parent
            data['class_name'] = my_class.name
            data['class_id'] = my_class.id
            if parent:
                data['parent_id'] = parent.id
                data['parent_name'] = parent.first_name + " " + parent.last_name
                data['parent_email'] = parent.email
                data['parent_phone'] = parent.phone
        return data


class AdminLoginTokenObtainPairPatchedSerializer(TokenObtainPairSerializer):

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.fields["email"] = serializers.EmailField()
        del self.fields['username']

    @map_exceptions(
        {
            InvalidPassword: ERROR_INVALID_PASSWORD,
            UserNotFound: ERROR_USER_NOT_FOUND,
        }
    )
    def validate(self, request_data):
        user = UserHandler().get_user_by_password(request_data)
        if user.role != UserType.ADMIN:
            raise UserNotFound('User Not Found')
        refresh = self.get_token(user)

        data = {
            "user": GetAllFieldUserSerializer(user, many=False).data,
            "refresh": str(refresh),
            "refresh_expired": refresh.current_time + refresh.lifetime,
            "access": str(refresh.access_token),
            "access_token_expired": refresh.current_time + refresh.access_token.lifetime,
        }
        role = user.role
        if role == UserType.PARENT:
            list_child = Student.objects.filter(
                parent_id=user.id
            ).select_related('user').select_related('my_class').values(
                'id',
                'user_id',
                'user__last_name',
                'user__first_name',
                'user__email',
                'user__date_of_birth',
                'my_class__name',
                'my_class__id',
            )
            res = []
            for student in list_child:
                res.append({
                    'student_id': student.get('id'),
                    'user_id': student.get('user_id'),
                    'full_name': student.get('user__first_name') + " " + student.get('user__last_name'),
                    'email': student.get('user__email'),
                    'date_of_birth': student.get('user__date_of_birth'),
                    'class_name': student.get('my_class__name'),
                    'class_id': student.get('my_class__id'),
                })
            data['info_child'] = res

        return {
            "success": True,
            "data": data
        }


class CustomizeTokenObtainPairPatchedSerializer(TokenObtainPairSerializer):

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.fields["email"] = serializers.EmailField()
        # self.fields["pin"] = serializers.IntegerField()
        # self.fields["token"] = serializers.CharField()
        del self.fields['username']
        # del self.fields['password']

    @map_exceptions(
        {
            InvalidPin: ERROR_INVALID_PIN,
            InvalidPassword: ERROR_INVALID_PASSWORD,
            UserNotFound: ERROR_USER_NOT_FOUND,
            PinNotExists: PIN_NOT_EXISTS,
            PinExpired: PIN_EXPIRED
        }
    )
    def validate(self, request_data):
        user = UserHandler().get_user_by_password(request_data)
        refresh = self.get_token(user)

        data = {
            "user": GetAllFieldUserSerializer(user, many=False).data,
            "refresh": str(refresh),
            "refresh_expired": refresh.current_time + refresh.lifetime,
            "access": str(refresh.access_token),
            "access_token_expired": refresh.current_time + refresh.access_token.lifetime,
        }
        role = user.role
        if role == UserType.PARENT:
            list_child = Student.objects.filter(
                parent_id=user.id
            ).select_related('user').select_related('my_class').values(
                'id',
                'user_id',
                'user__last_name',
                'user__first_name',
                'user__email',
                'user__date_of_birth',
                'my_class__name',
                'my_class__id',
            )
            res = []
            for student in list_child:
                res.append({
                    'student_id': student.get('id'),
                    'user_id': student.get('user_id'),
                    'full_name': student.get('user__first_name') + " " + student.get('user__last_name'),
                    'email': student.get('user__email'),
                    'date_of_birth': student.get('user__date_of_birth'),
                    'class_name': student.get('my_class__name'),
                    'class_id': student.get('my_class__id'),
                })
            data['info_child'] = res

        return {
            "success": True,
            "data": data
        }


class CustomerSignupSerializer(TokenObtainPairSerializer):
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.fields["email"] = serializers.EmailField()
        # self.fields["pin"] = serializers.IntegerField()
        # self.fields["token"] = serializers.CharField()
        self.fields["first_name"] = serializers.CharField()
        self.fields["last_name"] = serializers.CharField()

        del self.fields['username']
        # del self.fields['password']

    def validate(self, attrs):
        # pin = UserHandler().get_pin(attrs)
        required_fields = ['email', 'password', 'first_name', 'last_name']
        for field in required_fields:
            if self.initial_data.get(field, None) is None:
                logger_raise_warn_exception(field, error.RequireValue, detail=f"{field} is require")
            attrs[f'{field}'] = self.initial_data.get(field)
        # attrs['pin_object'] = pin
        return attrs

    def create(self, validated_data, **kwargs):
        email = validated_data.get('email')
        username = email.split("@")[0]
        try:
            user = User.objects.create(
                email=email,
                first_name=validated_data.get('first_name'),
                last_name=validated_data.get('last_name'),
                username=username,
                password=validated_data.get('password'),
            )
        except IntegrityError:
            user = User.objects.get(email=email)

        # pin_object = validated_data.get('pin_object')
        # pin_object.user = user
        refresh = self.get_token(user)
        # pin_object.save()

        # try:
        #     UserRole.objects.create(
        #         user=user,
        #         role=Role.objects.get(name=RoleName.CUSTOMER),
        #         is_active=True,
        #     )
        # except Role.DoesNotExist:
        #     raise RoleNotFound("The role is not exit")
        return {
            "refresh": str(refresh),
            "refresh_expired": refresh.current_time + refresh.lifetime,
            "access_token": str(refresh.access_token),
            "access_token_expired": refresh.current_time + refresh.access_token.lifetime,
        }


class CustomerAccountSerializer(serializers.Serializer):
    email = serializers.EmailField(max_length=200)
    phone = serializers.CharField(max_length=255)
    first_name = serializers.CharField(max_length=255)
    last_name = serializers.CharField(max_length=255)
