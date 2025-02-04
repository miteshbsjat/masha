"""
Module for creating and configuring logger instances.

This module provides a function to create a logger instance configured from a
logging configuration file. The logger is set up using the settings specified
in 'logging.conf'. If the configuration file is not found, a FileNotFoundError
is raised.
"""

import logging
import logging.config
from pathlib import Path


def create_logger(name):
    """
    Creates and returns a logger instance configured from a logging configuration file.

    Args:
        name (str): The name of the logger to be created.

    Returns:
        logging.Logger: A logger instance configured according to the settings
        in 'logging.conf'.

    Raises:
        FileNotFoundError: If the 'logging.conf' file is not found in the same
        directory as this script.
    """
    log_conf_file = Path(__file__).parent / "logging.conf"

    if not log_conf_file.exists():
        raise FileNotFoundError(
            f"The logging configuration file '{log_conf_file}' was not found."
        )

    logging.config.fileConfig(log_conf_file)
    return logging.getLogger(name)
