from datetime import datetime

from rest_framework import status
from rest_framework.exceptions import APIException
from rest_framework import views

from core.constants import ResultStatus


class PageNotFound(APIException):
    status_code = status.HTTP_404_NOT_FOUND
    default_detail = 'PageNotFound'
    default_code = 'not_found'


def custom_exception_handler(exc, context):
    # Call REST framework's default exception handler first,
    # to get the standard error response.
    response = views.exception_handler(exc, context)

    if response is not None:
        code = getattr(exc, 'default_code', status.HTTP_404_NOT_FOUND)
        message = getattr(exc, 'detail', '見つかりません')
        response.data = {
            'result': ResultStatus.FAILURE,
            'payload': None,
            'error': {
                'message': message,
                'code': code,
                'timestamp': datetime.now(),
            }
        }
        response.content_type = 'application/json'

    return response


class RequireValue(APIException):
    status_code = 400
    default_detail = 'required valu'
    default_code = 'required_value'
