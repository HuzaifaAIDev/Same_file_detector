"""
Central logging configuration.

Replaces ad-hoc print()/traceback.print_exc() calls with proper,
rotating, structured logs split by concern:
  - app.log      general application logs
  - error.log    warnings and above
  - access.log   HTTP access log (written by the access-log middleware)
  - security.log auth failures, rate-limit hits, rejected uploads, etc.
"""
import logging
import logging.handlers
from pathlib import Path

from app.core.config import settings

_CONFIGURED = False


def _make_handler(path: Path, level: int) -> logging.Handler:
    handler = logging.handlers.RotatingFileHandler(
        path, maxBytes=5 * 1024 * 1024, backupCount=5, encoding="utf-8"
    )
    handler.setLevel(level)
    handler.setFormatter(
        logging.Formatter(
            "%(asctime)s | %(levelname)-8s | %(name)s | %(message)s"
        )
    )
    return handler


def configure_logging() -> None:
    global _CONFIGURED
    if _CONFIGURED:
        return

    settings.LOG_DIR.mkdir(parents=True, exist_ok=True)

    root = logging.getLogger()
    root.setLevel(settings.LOG_LEVEL)

    console = logging.StreamHandler()
    console.setLevel(settings.LOG_LEVEL)
    console.setFormatter(logging.Formatter("%(levelname)-8s | %(name)s | %(message)s"))
    root.addHandler(console)

    root.addHandler(_make_handler(settings.LOG_DIR / "app.log", logging.INFO))
    root.addHandler(_make_handler(settings.LOG_DIR / "error.log", logging.WARNING))

    # Dedicated loggers (used explicitly by name, not via root propagation
    # duplication — they still propagate to root/app.log too, which is fine).
    logging.getLogger("security").addHandler(
        _make_handler(settings.LOG_DIR / "security.log", logging.INFO)
    )
    logging.getLogger("access").addHandler(
        _make_handler(settings.LOG_DIR / "access.log", logging.INFO)
    )

    _CONFIGURED = True


def get_logger(name: str) -> logging.Logger:
    configure_logging()
    return logging.getLogger(name)
