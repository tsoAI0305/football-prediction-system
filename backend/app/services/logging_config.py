import logging
import os
import builtins
from typing import Optional


def configure_logging(level: Optional[str] = None):
    """Configure root logging for the application.

    Reads LOG_LEVEL environment variable if level not provided.
    Also replaces built-in print with a thin wrapper that logs at INFO level
    so legacy print(...) statements are captured in logs when the
    application calls configure_logging early on.
    """
    lvl = (level or os.environ.get("LOG_LEVEL", "INFO")).upper()
    log_level = getattr(logging, lvl, logging.INFO)
    fmt = os.environ.get("LOG_FORMAT", "%(asctime)s %(levelname)s:%(name)s:%(message)s")
    datefmt = os.environ.get("LOG_DATEFMT", "%Y-%m-%d %H:%M:%S")

    logging.basicConfig(level=log_level, format=fmt, datefmt=datefmt)

    # Monkeypatch print to route to logging.info for backwards compatibility
    root_logger = logging.getLogger()

    def _print(*args, sep=" ", end="\n", file=None, flush=False):
        try:
            msg = sep.join(str(a) for a in args)
            # if printing to stderr, log as error
            if file is not None and hasattr(file, 'name') and file.name == '<stderr>':
                root_logger.error(msg)
            else:
                root_logger.info(msg)
        except Exception:
            root_logger.exception("Error in print wrapper")

    builtins.print = _print


# Convenience: auto-configure when app module imported in common entrypoints
# Avoid side-effects if module imported by unrelated tools; leave explicit call preferred.
