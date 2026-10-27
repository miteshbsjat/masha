"""
Logging configuration for MASHA.

Library modules obtain loggers with ``logging.getLogger(__name__)`` and never
configure handlers themselves. Only the CLI entry point calls
:func:`configure_logging`, so importing ``masha`` as a library never alters
the host application's logging setup.
"""

import logging
import sys

DEFAULT_FORMAT = "%(asctime)s | %(name)s | %(levelname)s | %(message)s"
DEFAULT_DATE_FORMAT = "%Y-%m-%d %H:%M:%S"

_HANDLER_NAME = "masha-cli"


def configure_logging(verbose: bool = False) -> None:
    """
    Configure the ``masha`` logger hierarchy for CLI use.

    Logs are written to ``stderr`` so they never mix with rendered output.
    Calling this function repeatedly is safe; the handler is installed once
    and only the level is updated.

    Args:
        verbose: If True, sets the log level to DEBUG; otherwise INFO.
    """
    level = logging.DEBUG if verbose else logging.INFO
    package_logger = logging.getLogger("masha")
    package_logger.setLevel(level)
    package_logger.propagate = False

    if not any(h.get_name() == _HANDLER_NAME for h in package_logger.handlers):
        handler = logging.StreamHandler(sys.stderr)
        handler.set_name(_HANDLER_NAME)
        handler.setFormatter(
            logging.Formatter(DEFAULT_FORMAT, datefmt=DEFAULT_DATE_FORMAT)
        )
        package_logger.addHandler(handler)


def create_logger(name: str, verbose: bool = False) -> logging.Logger:
    """
    Configure MASHA logging and return a named logger.

    Kept for backwards compatibility; new code should call
    :func:`configure_logging` once and use ``logging.getLogger(__name__)``.

    Args:
        name: The name of the logger to return.
        verbose: If True, sets the log level to DEBUG; otherwise INFO.

    Returns:
        A configured logging.Logger instance.
    """
    configure_logging(verbose=verbose)
    return logging.getLogger(name)
