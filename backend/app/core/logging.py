import json
import logging
import time
from datetime import datetime, timezone


class JSONFormatter(logging.Formatter):
    def format(self, record: logging.LogRecord) -> str:
        log_entry = {
            "timestamp": datetime.now(timezone.utc).isoformat(),
            "level": record.levelname,
            "logger": record.name,
            "message": record.getMessage(),
        }
        if record.exc_info and record.exc_info[0]:
            log_entry["exception"] = self.formatException(record.exc_info)
        if extra := getattr(record, "extra", None):
            log_entry.update(extra)
        return json.dumps(log_entry, ensure_ascii=False)


def setup_logging() -> None:
    root_logger = logging.getLogger()
    root_logger.setLevel(logging.INFO)

    handler = logging.StreamHandler()
    handler.setFormatter(JSONFormatter())
    for h in root_logger.handlers:
        root_logger.removeHandler(h)
    root_logger.addHandler(handler)

    logging.getLogger("uvicorn.access").handlers = []
    logging.getLogger("uvicorn.access").addHandler(handler)
    logging.getLogger("uvicorn.access").propagate = False

    logging.getLogger("sqlalchemy.engine").setLevel(logging.WARNING)
