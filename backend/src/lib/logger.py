"""Configuration du logging structuré"""
import logging
import sys
from typing import Any

from src.config import settings


class StructuredFormatter(logging.Formatter):
    """Formatter pour logs structurés avec contexte"""

    def format(self, record: logging.LogRecord) -> str:
        log_data = {
            "timestamp": self.formatTime(record, self.datefmt),
            "level": record.levelname,
            "logger": record.name,
            "message": record.getMessage(),
        }

        if hasattr(record, "extra"):
            log_data.update(record.extra)

        if record.exc_info:
            log_data["exception"] = self.formatException(record.exc_info)

        return str(log_data)


def setup_logging():
    """Configure le système de logging"""
    log_level = logging.DEBUG if settings.debug else logging.INFO

    handler = logging.StreamHandler(sys.stdout)
    handler.setLevel(log_level)
    handler.setFormatter(
        logging.Formatter(
            "%(asctime)s - %(name)s - %(levelname)s - %(message)s",
            datefmt="%Y-%m-%d %H:%M:%S",
        )
    )

    root_logger = logging.getLogger()
    root_logger.setLevel(log_level)
    root_logger.addHandler(handler)

    return root_logger


logger = setup_logging()
