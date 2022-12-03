import datetime
from pathlib import Path
import os
from urllib.parse import urljoin

# Build paths inside the project like this: BASE_DIR / 'subdir'.
BASE_DIR = Path(__file__).resolve().parent.parent

# Quick-start development settings - unsuitable for production
# See https://docs.djangoproject.com/en/3.2/howto/deployment/checklist/

# SECURITY WARNING: keep the secret key used in production secret!

SECRET_KEY = os.getenv("SECRET_KEY", "CHANGE_THIS_TO_SOMETHING_SECRET_IN_PRODUCTION")

# SECURITY WARNING: don't run with debug turned on in production!
DEBUG = os.getenv("DEBUG", False)

ALLOWED_HOSTS = "*"

# Application definition

DJANGO_APPS = (
    "polymorphic",
    'django.contrib.admin',
    "django.contrib.auth",
    "django.contrib.contenttypes",
    "django.contrib.sessions",
    "django.contrib.messages",
    "django.contrib.staticfiles",
)

THIRD_PARTY_APPS = (
    "rest_framework",
    "rest_framework_simplejwt.token_blacklist",
    "corsheaders",
    "channels",
    "drf_spectacular",
    "djcelery_email",
    "django_celery_beat",
    "rest_framework_swagger",
    "drf_yasg"
)

MY_CUSTOM_APPS = (
    "core",
    "api",
    # "ws",
)

INSTALLED_APPS = DJANGO_APPS + THIRD_PARTY_APPS + MY_CUSTOM_APPS

DJANGO_MIDDLEWARE = [
    "corsheaders.middleware.CorsMiddleware",
    'django.middleware.security.SecurityMiddleware',
    'django.contrib.sessions.middleware.SessionMiddleware',
    'django.middleware.common.CommonMiddleware',
    'django.middleware.csrf.CsrfViewMiddleware',
    'django.contrib.auth.middleware.AuthenticationMiddleware',
    'django.contrib.messages.middleware.MessageMiddleware',
    'django.middleware.clickjacking.XFrameOptionsMiddleware',
]
CUSTOM_MIDDLEWARE = [
    # 'utils.middlewares.ShowIpAddressMiddleware',
    # 'utils.middlewares.QueryCountDebugMiddleware'
]

MIDDLEWARE = DJANGO_MIDDLEWARE + CUSTOM_MIDDLEWARE

ROOT_URLCONF = 'config.urls'

TEMPLATES = [
    {
        'BACKEND': 'django.template.backends.django.DjangoTemplates',
        'DIRS': ['templates'],
        'APP_DIRS': True,
        'OPTIONS': {
            'context_processors': [
                'django.template.context_processors.debug',
                'django.template.context_processors.request',
                'django.contrib.auth.context_processors.auth',
                'django.contrib.messages.context_processors.messages',
            ],
        },
    },
]
WSGI_APPLICATION = "config.wsgi.application"
ASGI_APPLICATION = "config.asgi.application"

REDIS_HOST = os.getenv("REDIS_HOST", "redis")
REDIS_PORT = os.getenv("REDIS_PORT", "6379")
REDIS_USERNAME = os.getenv("REDIS_USER", "")
REDIS_PASSWORD = os.getenv("REDIS_PASSWORD", "")
REDIS_PROTOCOL = os.getenv("REDIS_PROTOCOL", "redis")
REDIS_URL = os.getenv(
    "REDIS_URL",
    f"{REDIS_PROTOCOL}://{REDIS_USERNAME}:{REDIS_PASSWORD}@{REDIS_HOST}:{REDIS_PORT}/0",
)
CELERY_BROKER_URL = REDIS_URL
CELERY_RESULT_BACKEND = REDIS_URL
CELERY_TRANSPORT = REDIS_URL
CELERY_TASK_ROUTES = {
}
CELERY_SOFT_TIME_LIMIT = 60 * 5
CELERY_TIME_LIMIT = CELERY_SOFT_TIME_LIMIT + 60

CELERY_REDBEAT_REDIS_URL = REDIS_URL
# Explicitly set the same value as the default loop interval here so we can use it
# later. CELERY_BEAT_MAX_LOOP_INTERVAL < CELERY_REDBEAT_LOCK_TIMEOUT must be kept true
# as otherwise a beat instance will acquire the lock, do scheduling, go to sleep for
# CELERY_BEAT_MAX_LOOP_INTERVAL before waking up where it assumes it still owns the lock
# however if the lock timeout is less than the interval the lock will have been released
# and the beat instance will crash as it attempts to extend the lock which it no longer
# owns.
CELERY_BEAT_MAX_LOOP_INTERVAL = os.getenv("CELERY_BEAT_MAX_LOOP_INTERVAL", 20)
# By default CELERY_REDBEAT_LOCK_TIMEOUT = 5 * CELERY_BEAT_MAX_LOOP_INTERVAL
# Only one beat instance can hold this lock and schedule tasks at any one time.
# This means if one celery-beat instance crashes any other replicas waiting to take over
# will by default wait 25 minutes until the lock times out and they can acquire
# the lock to start scheduling tasks again.
# Instead we just set it to be slightly longer than the loop interval that beat uses.
# This means beat wakes up, checks the schedule and extends the lock every
# CELERY_BEAT_MAX_LOOP_INTERVAL seconds. If it crashes or fails to wake up
# then 80 seconds after the lock was last extended it will be released and a new
# scheduler will acquire the lock and take over.
CELERY_REDBEAT_LOCK_TIMEOUT = os.getenv(
    "CELERY_REDBEAT_LOCK_TIMEOUT", int(CELERY_BEAT_MAX_LOOP_INTERVAL) + 60
)

CHANNEL_LAYERS = {
    "default": {
        "BACKEND": "channels_redis.core.RedisChannelLayer",
        "CONFIG": {
            "hosts": [REDIS_URL],
        },
    },
}

# Database
# https://docs.djangoproject.com/en/3.2/ref/settings/#databases

# DATABASES = {
#     'default': {
#         'ENGINE': 'django.db.backends.sqlite3',
#         'NAME': BASE_DIR.parent / 'db.sqlite3',
#     }
# }

USER_TABLE_DATABASE = "default"

AUTH_USER_MODEL = "core.User"

# Password validation
# https://docs.djangoproject.com/en/3.2/ref/settings/#auth-password-validators

AUTH_PASSWORD_VALIDATORS = [
    {
        "NAME": "django.contrib.auth.password_validation.MinimumLengthValidator",
    },
    {
        "NAME": "core.utils.MaximumLengthValidator",
    },
]

# We need the `AllowAllUsersModelBackend` in order to respond with a proper error
# message when the user is not active. The only thing it does, is allowing non active
# users to authenticate, but the user still can't obtain or use a JWT token or database
# token because the user needs to be active to use that.
AUTHENTICATION_BACKENDS = ["django.contrib.auth.backends.AllowAllUsersModelBackend"]

# Internationalization
# https://docs.djangoproject.com/en/3.2/topics/i18n/

LANGUAGE_CODE = 'en'

LANGUAGES = [
    ("en", "English"),
]

TIME_ZONE = 'UTC'

USE_I18N = True

USE_L10N = True

USE_TZ = False

# Static files (CSS, JavaScript, Images)
# https://docs.djangoproject.com/en/3.2/howto/static-files/

STATIC_URL = '/static/'

# Default primary key field type
# https://docs.djangoproject.com/en/3.2/ref/settings/#default-auto-field

DEFAULT_AUTO_FIELD = 'django.db.models.BigAutoField'

REST_FRAMEWORK = {
    "DEFAULT_PERMISSION_CLASSES": ("rest_framework.permissions.IsAuthenticated",),
    "DEFAULT_AUTHENTICATION_CLASSES": (
        "core.authentication.JSONWebTokenAuthentication",
        "rest_framework_simplejwt.authentication.JWTAuthentication",
    ),
    "DEFAULT_RENDERER_CLASSES": ("rest_framework.renderers.JSONRenderer",),
    # "DEFAULT_SCHEMA_CLASS": "core.openapi.AutoSchema",
    "DEFAULT_SCHEMA_CLASS": 'rest_framework.schemas.coreapi.AutoSchema',
    'DEFAULT_PAGINATION_CLASS': 'utils.pagination.PageNumberPagination',
    'PAGE_SIZE': 100,
    'EXCEPTION_HANDLER': 'utils.error.custom_exception_handler'
}

CORS_ORIGIN_ALLOW_ALL = True
CORS_ALLOW_CREDENTIALS = True
CORS_ALLOW_ALL_ORIGINS = True

CORS_ALLOW_HEADERS = ["*"]

# CORS_ALLOWED_ORIGINS = ['*']

JWT_AUTH = {
    "JWT_EXPIRATION_DELTA": datetime.timedelta(days=30),
    "JWT_ALLOW_REFRESH": True,
    "JWT_REFRESH_EXPIRATION_DELTA": datetime.timedelta(days=90),
    "JWT_AUTH_HEADER_PREFIX": "JWT",
    "JWT_RESPONSE_PAYLOAD_HANDLER": "core.jwt.jwt_response_payload_handler",
}
SIMPLE_JWT = {
    'ACCESS_TOKEN_LIFETIME': datetime.timedelta(days=30),
    'REFRESH_TOKEN_LIFETIME': datetime.timedelta(days=90),
}

SPECTACULAR_SETTINGS = {
    "TITLE": "API SPEC BY HIENCODAY ",
    "DESCRIPTION": "This app build by HIENCODAY",
    "CONTACT": {"url": "https://facebook.com/gh3698"},
    "LICENSE": {
        "name": "MIT",
        "url": "https://github.com",
    },
    "VERSION": "1.7.1",
    "SERVE_INCLUDE_SCHEMA": False,
    "TAGS": [
        {"name": "Settings"},
        {"name": "User"},
        {"name": "User files"},
        {"name": "Groups"},
        {"name": "Group invitations"},
        {"name": "Templates"},
        {"name": "Trash"},
        {"name": "Applications"},
        {"name": "Database tables"},
        {"name": "Database table fields"},
        {"name": "Database table views"},
        {"name": "Database table view filters"},
        {"name": "Database table view sortings"},
        {"name": "Database table grid view"},
        {"name": "Database table gallery view"},
        {"name": "Database table form view"},
        {"name": "Database table kanban view"},
        {"name": "Database table rows"},
        {"name": "Database table export"},
        {"name": "Database table webhooks"},
        {"name": "Database tokens"},
        {"name": "Admin"},
    ],
    "ENUM_NAME_OVERRIDES": {
        "NumberDecimalPlacesB02Enum": [
            (0, "1"),
            (1, "1.0"),
            (2, "1.00"),
            (3, "1.000"),
            (4, "1.0000"),
            (5, "1.00000"),
        ],
        "NumberDecimalPlaces0c0Enum": [
            (1, "1.0"),
            (2, "1.00"),
            (3, "1.000"),
            (4, "1.0000"),
            (5, "1.00000"),
        ],
    },
}

# The storage must always overwrite existing files.
DEFAULT_FILE_STORAGE = "core.storage.OverwriteFileSystemStorage"

FROM_EMAIL = os.getenv("FROM_EMAIL", "")
RESET_PASSWORD_TOKEN_MAX_AGE = 60 * 60 * 48  # 48 hours
ROW_PAGE_SIZE_LIMIT = 200  # How many rows can be requested at once.
TRASH_PAGE_SIZE_LIMIT = 200  # How many trash entries can be requested at once.
ROW_COMMENT_PAGE_SIZE_LIMIT = 200  # How many row comments can be requested at once.

PUBLIC_BACKEND_URL = os.getenv("PUBLIC_BACKEND_URL", "http://localhost:8000")
MEDIA_URL_PATH = "/media/"
MEDIA_URL = os.getenv("MEDIA_URL", urljoin(PUBLIC_BACKEND_URL, MEDIA_URL_PATH))
MEDIA_ROOT = os.getenv("MEDIA_ROOT", "/base_django/media")

# Indicates the directory where the user files and user thumbnails are stored.
USER_FILES_DIRECTORY = "user_files"
USER_THUMBNAILS_DIRECTORY = "thumbnails"
USER_FILE_SIZE_LIMIT = 1024 * 1024 * 20  # 20MB

EXPORT_FILES_DIRECTORY = "export_files"
EXPORT_CLEANUP_INTERVAL_MINUTES = 5
EXPORT_FILE_EXPIRE_MINUTES = 60

# FOR SEND EMAIL
EMAIL_BACKEND = "djcelery_email.backends.CeleryEmailBackend"

if os.getenv("EMAIL_SMTP", "SMTP"):
    CELERY_EMAIL_BACKEND = "django.core.mail.backends.smtp.EmailBackend"
    EMAIL_BACKEND = 'django.core.mail.backends.smtp.EmailBackend'  # "django_smtp_ssl.SSLEmailBackend"  # 'django.core.mail.backends.smtp.EmailBackend'
    # EMAIL_SMTP_USE_TLS for backwards compatibility after
    # fixing #448.
    EMAIL_USE_TLS = True
    EMAIL_HOST = os.getenv("EMAIL_SMTP_HOST", "")
    EMAIL_PORT = os.getenv("EMAIL_SMTP_PORT", "")
    EMAIL_HOST_USER = os.getenv("EMAIL_SMTP_USER", '')
    EMAIL_HOST_PASSWORD = os.getenv("EMAIL_SMTP_PASSWORD", "")

else:
    CELERY_EMAIL_BACKEND = "django.core.mail.backends.console.EmailBackend"

CELERY_EMAIL_TASK_CONFIG = {
    'name': 'djcelery_email_send_multiple',
    'ignore_result': False,
}
CELERY_EMAIL_CHUNK_SIZE = 1

# Configurable thumbnails that are going to be generated when a user uploads an image
# file.
USER_THUMBNAILS = {"tiny": [None, 21], "small": [48, 48]}

# For now force the old os dependant behaviour of file uploads as users might be relying
# on it. See
# https://docs.djangoproject.com/en/3.2/releases/3.0/#new-default-value-for-the-file-upload-permissions-setting
FILE_UPLOAD_PERMISSIONS = None

MAX_FORMULA_STRING_LENGTH = 10000
MAX_FIELD_REFERENCE_DEPTH = 1000
UPDATE_FORMULAS_AFTER_MIGRATION = bool(
    os.getenv("UPDATE_FORMULAS_AFTER_MIGRATION", "yes")
)

WEBHOOKS_MAX_CONSECUTIVE_TRIGGER_FAILURES = 8
WEBHOOKS_MAX_RETRIES_PER_CALL = 8
WEBHOOKS_MAX_PER_TABLE = 20
WEBHOOKS_MAX_CALL_LOG_ENTRIES = 10
WEBHOOKS_REQUEST_TIMEOUT_SECONDS = 5

PIN_EXPIRATION_DELTA = datetime.timedelta(minutes=5)

MAX_FIELD_LIMIT = 1500
DEFAULT_PAGINATION_PAGE_SIZE = 100

CHANNEL_CHAT_REDIS = os.getenv("CHANNEL_CHAT_REDIS", "private-chat-app")
