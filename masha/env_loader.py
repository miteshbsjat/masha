"""
Load environment variables into configuration values.
"""

import logging
import os
import re
from typing import Any

logger = logging.getLogger(__name__)

_ENV_PATTERN = re.compile(r"\$\{(\w+):\s*(.*?)\}")


def _resolve_value(value: Any) -> Any:
    if isinstance(value, str):
        match = _ENV_PATTERN.fullmatch(value)
        if match:
            env_var, default_value = match.groups()
            if env_var in os.environ:
                # Never log the value itself: it may be a secret.
                logger.debug("Resolved env variable %s", env_var)
                return os.environ[env_var]
            logger.debug("Env variable %s not set, using default", env_var)
            return None if default_value == "null" else default_value
        return value
    if isinstance(value, dict):
        return {k: _resolve_value(v) for k, v in value.items()}
    if isinstance(value, list):
        return [_resolve_value(v) for v in value]
    return value


def resolve_env_variables(config: Any) -> Any:
    """
    Resolve environment variables in a configuration dictionary.

    Searches for environment variable placeholders in the given configuration.
    Placeholders use the format ${ENV_VAR:default_value}, where ENV_VAR is
    the environment variable name and default_value is optional. A default of
    ``null`` resolves to ``None``.

    Args:
        config: The configuration dictionary (or nested structure) containing
                potential environment variable placeholders. It is not
                mutated.

    Returns:
        A new structure with all environment variable placeholders resolved.
    """
    return _resolve_value(config)
