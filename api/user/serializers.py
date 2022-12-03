from django.contrib.auth.models import update_last_login
from rest_framework import serializers
from rest_framework_jwt.serializers import JSONWebTokenSerializer

from core.models import User, UserPin, UserType
from core.users.handler import UserHandler
from core.users.utils import normalize_email_address
from custom_service.models.ModelTechwiz import Student, MyClass, ClassTeacherSubject
from utils import error
from utils.logger import logger_raise_warn_exception
from utils.validators import password_validation, validate_phone_number


class GetUserChatSerializer(serializers.Serializer):
    """
        nếu là student thì có thông tin lớp, với email + sđt
        nếu là parent thì có thông tin con, lớp của con, với email & sđt
        nếu là teacher thì có list các lớp đang dạy kèm môn, với email + sđt
    """
    info = serializers.SerializerMethodField()

    def get_info(self, instance):
        if instance.role == UserType.STUDENT:
            student = Student.objects.filter(user_id=instance.id).select_related('my_class').first()
            return {
                "role": instance.role,
                "email": instance.email,
                "phone": instance.phone,
                "first_name": instance.first_name,
                "last_name": instance.last_name,
                "user_id": instance.id,
                "student_id": student.id,
                "class_name": student.my_class.name,
            }
        elif instance.role == UserType.PARENT:
            students = Student.objects.filter(parent_id=instance.id).select_related('my_class', 'user').all()
            details = []
            if len(students):
                for item in students:
                    details.append({
                        "student_id": item.user.id,
                        "student_email": item.user.email,
                        "student_phone": item.user.phone,
                        "student_first_name": item.user.first_name,
                        "student_last_name": item.user.last_name,
                        "class_name": item.my_class.name,
                        "class_id": item.my_class.id,
                    })
            return {
                "role": instance.role,
                "email": instance.email,
                "phone": instance.phone,
                "first_name": instance.first_name,
                "last_name": instance.last_name,
                "user_id": instance.id,
                'details': details
            }
        elif instance.role == UserType.TEACHER:
            list_class_teacher_sub = ClassTeacherSubject.objects.filter(
                teacher_id=instance.id
            ).select_related(
                'my_class',
                'subject'
            ).all()
            details = []
            if len(list_class_teacher_sub):
                for item in list_class_teacher_sub:
                    details.append({
                        'subject_id': item.subject.id,
                        'subject_name': item.subject.name,
                        'class_id': item.my_class.id,
                        'class_name': item.my_class.name
                    })
            return {
                "role": instance.role,
                "email": instance.email,
                "phone": instance.phone,
                "first_name": instance.first_name,
                "last_name": instance.last_name,
                "user_id": instance.id,
                "details": details
            }
        return None


class GetUserSerializer(serializers.ModelSerializer):
    class Meta:
        model = User
        fields = ("role", "email", "phone", "first_name", "last_name", "date_of_birth", "address", "avatar_url", "id")
        extra_kwargs = {
            "id": {"read_only": True},
        }


class UserSerializer(serializers.ModelSerializer):
    class Meta:
        model = User
        fields = ("email", "phone", "first_name", "last_name", "username", "id")
        extra_kwargs = {
            "id": {"read_only": True},
        }


class UpdateUserSerializer(serializers.Serializer):
    first_name = serializers.CharField(max_length=150, required=False)
    last_name = serializers.CharField(max_length=150, required=False)
    phone = serializers.CharField(max_length=15, validators=[validate_phone_number], required=False)
    avatar_url = serializers.CharField(max_length=255, required=False)
    address = serializers.CharField(max_length=255, required=False)
    date_of_birth = serializers.DateTimeField(required=False)
    id = serializers.IntegerField(required=True)


class RegisterSerializer(serializers.Serializer):
    family_name = serializers.CharField(max_length=150)
    given_name = serializers.CharField(max_length=150)
    email = serializers.EmailField(
        help_text="The email address is also going to be the username."
    )
    password = serializers.CharField(validators=[password_validation])
    authenticate = serializers.BooleanField(
        required=False,
        default=False,
        help_text="Indicates whether an authentication token should be generated and "
                  "be included in the response.",
    )


class ChangePasswordBodyValidationSerializer(serializers.Serializer):
    old_password = serializers.CharField()
    new_password = serializers.CharField(validators=[password_validation])


class ForgotPasswordBodyValidationSerializer(serializers.Serializer):
    email = serializers.EmailField(required=True)
    pin = serializers.IntegerField(required=True)
    token = serializers.CharField(max_length=300, required=True)
    new_password = serializers.CharField(required=True, validators=[password_validation])

    def validate(self, attrs):
        required_fields = ['email', 'new_password', 'pin', 'token']
        for field in required_fields:
            if self.initial_data.get(field, None) is None:
                logger_raise_warn_exception(field, error.RequireValue, detail=f"{field} is require")
            attrs[f'{field}'] = self.initial_data.get(field)

        user_pin = UserHandler().get_pin(attrs)
        attrs['user_pin'] = user_pin
        return attrs


class ResetPasswordBodyValidationSerializer(serializers.Serializer):
    token = serializers.CharField()
    password = serializers.CharField(validators=[password_validation])


class SendResetPasswordEmailBodyValidationSerializer(serializers.Serializer):
    email = serializers.EmailField(
        help_text="The email address of the user that has requested a password reset."
    )
    base_url = serializers.URLField(
        help_text="The base URL where the user can reset his password. The reset "
                  "token is going to be appended to the base_url (base_url "
                  "'/token')."
    )


class NormalizedEmailField(serializers.EmailField):
    def to_internal_value(self, data):
        data = super().to_internal_value(data)
        return normalize_email_address(data)


class NormalizedEmailWebTokenSerializer(JSONWebTokenSerializer):
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.fields[self.username_field] = NormalizedEmailField()

    def validate(self, attrs):
        """
        This serializer is only used by the ObtainJSONWebToken view which is only used
        to generate a new token. When that happens we want to update the user's last
        login timestamp.
        """

        # In the future, when migrating away from the JWT implementation, we want to
        # respond with machine readable error codes when authentication fails.
        validated_data = super().validate(attrs)

        user = validated_data["user"]
        if not user.is_active:
            msg = "User account is disabled."
            raise serializers.ValidationError(msg)

        update_last_login(None, user)
        # UserLogEntry.objects.create(actor=user, action="SIGNED_IN")
        # Call the user_signed_in method for each plugin that is un the registry to
        # notify all plugins that a user has signed in.
        from core.registries import plugin_registry

        for plugin in plugin_registry.registry.values():
            plugin.user_signed_in(user)
        return validated_data
