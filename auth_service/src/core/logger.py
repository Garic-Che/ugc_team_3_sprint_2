import json
import os
from pythonjsonlogger import jsonlogger  # pip install python-json-logger

LOG_FORMAT = '{"request_id": "%(request_id)s", "asctime": \
             "%(asctime)s", "levelname": "%(levelname)s", \
             "name": "%(name)s", "message": "%(message)s", \
             "host": "%(host)s", "user-agent": "%(user-agent)s", "method": "%(method)s", "path": "%(path)s", \
             "query_params": "%(query_params)s", "status_code": "%(status_code)s"}'

class CustomJsonFormatter(jsonlogger.JsonFormatter):
    def add_fields(self, log_record, record, message_dict):
        super().add_fields(log_record, record, message_dict)
        log_record.update({
            "timestamp": self.formatTime(record),
            "level": record.levelname,
            "service": record.name,
            "environment": os.getenv("ENVIRONMENT", "dev"),
            "trace_id": record.__dict__.get('trace_id', ''),
            "span_id": record.__dict__.get('span_id', ''),
            "commit_hash": os.getenv("COMMIT_HASH", "")
        })

LOG_DEFAULT_HANDLERS = ["json_console"]

LOGGING = {
    "version": 1,
    "disable_existing_loggers": False,
    "formatters": {
        "verbose": {
            "()": CustomJsonFormatter,
            "format": LOG_FORMAT,
            "rename_fields": {"levelname": "severity", "asctime": "timestamp"},
            "json_ensure_ascii": False
        },
        "default": {
            "()": "uvicorn.logging.DefaultFormatter",
            "fmt": "%(levelprefix)s %(message)s",
            "use_colors": None,
        },
        "access": {
            "()": "uvicorn.logging.AccessFormatter",
            "fmt": ("%(levelprefix)s %(client_addr)s - "
                    "'%(request_line)s' %(status_code)s"),
        },
    },
    "handlers": {
        "json_console": {
            "level": "DEBUG",
            "class": "logging.StreamHandler",
            "formatter": "verbose",
            "stream": "ext://sys.stdout"
        },
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
        "uvicorn.error": {
            "level": "INFO",
        },
        "uvicorn.access": {
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
