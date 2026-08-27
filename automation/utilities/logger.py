import json
import logging
import os
import sys
from datetime import datetime, timezone
from pathlib import Path


class JsonLogFormatter(logging.Formatter):
    """ELK-compatible structured JSON log formatter for enterprise audit logging."""
    def format(self, record: logging.LogRecord) -> str:
        log_obj = {
            "@timestamp": datetime.fromtimestamp(record.created, tz=timezone.utc).isoformat(),
            "level": record.levelname,
            "logger": record.name,
            "message": record.getMessage(),
            "module": record.module,
            "function": record.funcName,
            "line": record.lineno,
            "environment": os.getenv("ENV", "local")
        }
        if record.exc_info:
            log_obj["exception"] = self.formatException(record.exc_info)
        return json.dumps(log_obj)


def get_logger(name: str = "QE_Platform") -> logging.Logger:
    """Returns a configured structured logger with console, text file, and ELK JSON handlers."""
    logger = logging.getLogger(name)

    if logger.hasHandlers():
        return logger

    logger.setLevel(logging.INFO)

    # Standard Formatter
    formatter = logging.Formatter(
        "[%(asctime)s] [%(levelname)s] [%(name)s] %(message)s",
        datefmt="%Y-%m-%d %H:%M:%S"
    )

    # Console Handler
    console_handler = logging.StreamHandler(sys.stdout)
    console_handler.setFormatter(formatter)
    logger.addHandler(console_handler)

    # Log directory setup
    log_dir = Path(__file__).parent.parent.parent / "logs"
    log_dir.mkdir(exist_ok=True)

    today_str = datetime.now().strftime("%Y-%m-%d")
    file_handler = logging.FileHandler(log_dir / f"execution_{today_str}.log", encoding="utf-8")
    file_handler.setFormatter(formatter)
    logger.addHandler(file_handler)

    # ELK-ready JSON Log Handler
    json_handler = logging.FileHandler(log_dir / "audit_json.log", encoding="utf-8")
    json_handler.setFormatter(JsonLogFormatter())
    logger.addHandler(json_handler)

    return logger

