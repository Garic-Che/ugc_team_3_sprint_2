LOG_FORMAT = '{"request_id": "%(request_id)s", "asctime": \
             "%(asctime)s", "levelname": "%(levelname)s", \
             "name": "%(name)s", "message": "%(message)s", \
             "host": "%(host)s", "user-agent": "%(user-agent)s", "method": "%(method)s", "path": "%(path)s", \
             "query_params": "%(query_params)s", "status_code": "%(status_code)s"}'
LOG_DEFAULT_HANDLERS = [
    "console",
]

# В логгере настраивается логгирование gunicorn-сервера.
# Про логирование в Python можно прочитать в документации
# https://docs.python.org/3/howto/logging.html
# https://docs.python.org/3/howto/logging-cookbook.html

LOGGING = {
    "version": 1,
    "disable_existing_loggers": False,
    "formatters": {
        "verbose": {"format": LOG_FORMAT},
        "default": {
            "format": "%(levelname)s: %(message)s",
        },
        "access": {
            "format": "%(asctime)s - %(name)s - %(levelname)s - %(message)s",
        },
    },
    "handlers": {
        "console": {
            "level": "DEBUG",
            "class": "logging.StreamHandler",
            "formatter": "verbose",
        },
        "default": {
            "formatter": "default",
            "class": "logging.StreamHandler",
            "stream": "ext://sys.stdout",
        },
        "access": {
            "formatter": "access",
            "class": "logging.StreamHandler",
            "stream": "ext://sys.stdout",
        },
    },
    "loggers": {
        "": {
            "handlers": LOG_DEFAULT_HANDLERS,
            "level": "INFO",
        },
        "gunicorn.error": {
            "level": "INFO",
        },
        "gunicorn.access": {
            "handlers": ["access"],
            "level": "INFO",
            "propagate": False,
        },
    },
    "root": {
        "level": "INFO",
        "formatter": "verbose",
        "handlers": LOG_DEFAULT_HANDLERS,
    },
}
