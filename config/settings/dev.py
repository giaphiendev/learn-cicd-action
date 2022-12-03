from .base import *  # noqa: F403, F401

if os.getenv("ON_LOGS", False):
    import errno
    LOG_DIR = "/var/log/base_django/"
    if not os.path.exists(os.path.dirname(LOG_DIR)):
        try:
            os.makedirs(os.path.dirname(LOG_DIR))
        except OSError as exc:  # Guard against race condition
            if exc.errno != errno.EEXIST:
                raise

    ALLOWED_HOSTS = "*"

    LOGGING = {
        "version": 1,
        "disable_existing_loggers": False,
        "formatters": {
            "verbose": {
                "format": "[%(levelname)s]\t%(asctime)s\t%(name)s\t%(module)s.%(funcName)s:%(lineno)s\t%(message)s",
                "datefmt": "%Y-%m-%d %H:%M:%S %z",
            },
        },
        "handlers": {
            "console": {
                "level": "DEBUG",
                "class": "logging.StreamHandler",
                "formatter": "verbose",
            },
            'app': {
                'level': 'DEBUG',
                'class': 'logging.handlers.TimedRotatingFileHandler',
                'filename': f'/var/log/base_django/app.log',
                'formatter': 'verbose',
            },
            'info': {
                'level': 'DEBUG',
                'class': 'logging.handlers.TimedRotatingFileHandler',
                'filename': f'/var/log/base_django/info.log',
                'formatter': 'verbose',
            },
            'error': {
                'level': 'ERROR',
                'class': 'logging.handlers.TimedRotatingFileHandler',
                'filename': f'/var/log/base_django/error.log',
                'formatter': 'verbose',
            },
        },
        'loggers': {
            'django': {
                "handlers": ["console", "app", "error"],
                'level': 'INFO',
                'propagate': True,
            },
            "custom_logger": {
                "level": "INFO",
                "handlers": ["console", "app", "error", 'info'],
                'propagate': True,
            },
        },
        "root": {
            "level": "INFO",
            "handlers": ["console", "app", "error"],
            'propagate': True,
        },
    }

try:
    from .local import *  # noqa: F403, F401
except ImportError:
    pass
