import json
import logging
import sys
from datetime import UTC, datetime
from typing import TextIO

from app.config import DEBUG


SAFE_LOG_FIELDS = (
    "stage",
    "result_count",
    "status_code",
    "error_type",
    "limit",
)


class JsonLogFormatter(logging.Formatter):
    """Serialize only explicitly approved, non-sensitive log fields."""

    def format(self, record: logging.LogRecord) -> str:
        payload: dict[str, object] = {
            "timestamp": datetime.now(UTC).isoformat(),
            "level": record.levelname.lower(),
            "logger": record.name,
            "event": record.getMessage(),
        }

        for field in SAFE_LOG_FIELDS:
            value = getattr(record, field, None)
            if value is not None:
                payload[field] = value

        return json.dumps(payload, separators=(",", ":"))


def configure_logging(
    *,
    debug: bool | None = None,
    stream: TextIO | None = None,
) -> logging.Logger:
    """Configure Tripzy's structured application logger."""

    logger = logging.getLogger("tripzy")
    logger.handlers.clear()
    logger.propagate = False
    logger.setLevel(
        logging.DEBUG if (DEBUG if debug is None else debug) else logging.INFO
    )

    handler = logging.StreamHandler(stream or sys.stdout)
    handler.setFormatter(JsonLogFormatter())
    logger.addHandler(handler)

    return logger


logger = configure_logging()
