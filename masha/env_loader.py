#!/usr/bin/env python3

"""
Loads the environment variable in configuration value
"""

import json
import os
import re
from pathlib import Path

from returns.result import Failure, Success

# pylint: disable=W1203
from masha.config_loader import load_and_merge_configs
from masha.logger_factory import create_logger

logger = create_logger("masha")

_path_matcher = re.compile(
    r"\$\{(?P<env_name>[^}^{:]+)(?::(?P<default_value>[^}^{]*))?\}"
)


def resolve_env_variables(config) -> dict:
    """
    Resolve environment variables in a configuration dictionary.

    This function recursively searches for environment variable placeholders in
    the given configuration. Placeholders are in the format ${ENV_VAR: default_value},
    where ENV_VAR is the name of the environment variable and default_value is an
    optional default value if the environment variable is not set.

    Args:
        config (dict): The configuration dictionary containing potential environment
                       variable placeholders.

    Returns:
        dict: A new dictionary with all environment variable placeholders resolved.
    """
    pattern = re.compile(
        r"\$\{(\w+):\s*(.*?)\}"
    )  # Match ${ENV_VAR: default_value}

    def resolve_value(value):
        if isinstance(value, str):
            match = pattern.fullmatch(value)
            if match:
                env_var, default_value = match.groups()
                if default_value == "null":
                    default_value = None
                return os.getenv(env_var, default_value)
        elif isinstance(
            value, dict
        ):  # Recursively resolve nested dictionaries
            return {k: resolve_value(v) for k, v in value.items()}
        elif isinstance(value, list):  # Recursively resolve lists
            return [resolve_value(v) for v in value]
        return value  # Return unchanged if no match

    return {key: resolve_value(value) for key, value in config.items()}


def main():
    """
    Validates merged configuration files against a Pydantic model.

    This function sets up an argument parser to accept paths to configuration files.
    It then loads and merges these configuration files, printing the merged result in JSON format.
    """
    conf_file = Path(__file__).parent.parent / "test" / "env_config.yaml"
    config = None
    match load_and_merge_configs([conf_file]):
        case Success(value):
            config = value
        case Failure(value):
            logger.warning(f"Failed to read configs: {value}")
            return
    logger.debug(f"config = {config}")
    os.environ["ENV_B"] = "default_not_used_b"
    env_config = resolve_env_variables(config)
    logger.debug(f"env_config = {json.dumps(env_config)}")


if __name__ == "__main__":
    main()
