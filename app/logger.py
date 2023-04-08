import logging
import logging.config
import structlog
from settings import settings


def configure_logger():
    """Configure the logger to use throughout the project

    Uses these variables from settings:
        LOG_LEVEL -- The loglevel to use
    """

    logging.config.dictConfig(
        {
            "version": 1,
            "disable_existing_loggers": False,
            "formatters": {
                "plain": {
                    "()": structlog.stdlib.ProcessorFormatter,
                    "processor": structlog.processors.JSONRenderer(sort_keys=True),
                },
                "colored": {
                    "()": structlog.stdlib.ProcessorFormatter,
                    "processor": structlog.dev.ConsoleRenderer(colors=True),
                },
            },
            "handlers": {
                "default": {
                    "level": settings.LOG_LEVEL,
                    "class": "logging.StreamHandler",
                    "formatter": "colored",
                },
                "file": {
                    "level": settings.LOG_LEVEL,
                    "class": "logging.handlers.TimedRotatingFileHandler",
                    "filename": settings.LOG_FILE,
                    "when": "d",
                    "backupCount": 3,
                    "formatter": "plain",
                },
            },
            "loggers": {
                "log": {
                    "handlers": ["default", "file"],
                    "level": settings.LOG_LEVEL,
                    "propagate": False,
                },
            },
        }
    )
    structlog.configure(
        processors=[
            structlog.stdlib.add_logger_name,
            structlog.stdlib.add_log_level,
            structlog.stdlib.PositionalArgumentsFormatter(),
            structlog.processors.TimeStamper(fmt="iso"),
            structlog.processors.StackInfoRenderer(),
            structlog.processors.format_exc_info,
            structlog.stdlib.ProcessorFormatter.wrap_for_formatter,
        ],
        context_class=dict,
        logger_factory=structlog.stdlib.LoggerFactory(),
        wrapper_class=structlog.stdlib.BoundLogger,
        cache_logger_on_first_use=True,
    )


def get_logger(name: str) -> logging.Logger:
    """ Returns a logger object with proper name

    Parameters
    ----------
    name : str
        name of the logger

    Returns
    -------
    logging.Logger
        logger object
    """
    return structlog.get_logger(f"log.{name}")
