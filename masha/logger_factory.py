"""
Module for creating and configuring logger instances.

This module provides a function to create a logger instance. It attempts to
load settings from 'logging.conf', falling back to a sensible default
configuration if the file is not found.
"""

import logging
import logging.config
from pathlib import Path


_DEFAULT_FORMAT = "%(asctime)s | %(name)s | %(levelname)s | %(message)s"
_DEFAULT_DATE_FORMAT = "%Y-%m-%d %H:%M:%S"


def create_logger(name: str, verbose: bool = False) -> logging.Logger:
    """
    Creates and returns a logger instance.

    Attempts to load configuration from 'logging.conf'. If the file is not
    found, falls back to a basic configuration with the standard format.

    Args:
        name: The name of the logger to be created.
        verbose: If True, sets the log level to DEBUG; otherwise INFO.

    Returns:
        A configured logging.Logger instance.
    """
    log_conf_file = Path(__file__).parent / "logging.conf"

    try:
        logging.config.fileConfig(log_conf_file)
    except FileNotFoundError:
        # Fallback to basic configuration
        logging.basicConfig(
            level=logging.DEBUG if verbose else logging.INFO,
            format=_DEFAULT_FORMAT,
            datefmt=_DEFAULT_DATE_FORMAT,
        )

    logger = logging.getLogger(name)

    # Override level based on verbose flag if using fallback config
    if not log_conf_file.exists():
        logger.setLevel(logging.DEBUG if verbose else logging.INFO)

    return logger
