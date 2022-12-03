import re
from rest_framework import serializers

from django.contrib.auth.password_validation import validate_password
from django.core.exceptions import ValidationError


def validate_phone_number(value):
    if not re.match('^[0-9]{8,12}$', value):
        raise serializers.ValidationError(u'The phone is invalid')


def validate_postal_code(value):
    if not re.match('^\d{6,7}$', value):
        raise serializers.ValidationError(u'The postal code is invalid')


def password_validation(value):
    """
    Verifies that the provided password adheres to the password validation as defined
    in the django core settings.
    """

    try:
        validate_password(value)
    except ValidationError as e:
        raise serializers.ValidationError(
            e.messages[0], code="password_validation_failed"
        )

    return value
