"""
Load environment variables into configuration values.
"""

import logging
import os
import re
from typing import Any

from masha.logger_factory import create_logger

logger = create_logger("masha")

_env_pattern = re.compile(r"\$\{(\w+):\s*(.*?)\}")


def resolve_env_variables(config: Any) -> Any:
    """
    Resolve environment variables in a configuration dictionary.

    Searches for environment variable placeholders in the given configuration.
    Placeholders use the format ${ENV_VAR:default_value}, where ENV_VAR is
    the environment variable name and default_value is optional.

    Args:
        config: The configuration dictionary (or nested structure) containing
                potential environment variable placeholders.

    Returns:
        A new structure with all environment variable placeholders resolved.
    """
    def resolve_value(value):
        if isinstance(value, str):
            match = _env_pattern.fullmatch(value)
            if match:
                env_var, default_value = match.groups()
                if default_value == "null":
                    default_value = None
                return os.getenv(env_var, default_value)
        elif isinstance(value, dict):
            return {k: resolve_value(v) for k, v in value.items()}
        elif isinstance(value, list):
            return [resolve_value(v) for v in value]
        return value

    if isinstance(config, dict):
        return {key: resolve_value(value) for key, value in config.items()}
    return config
