#!/usr/bin/env python3

import re
import os
import json
import logging
from pathlib import Path
import config_loader

from logger_factory import create_logger
logger = create_logger("masha")

_path_matcher = re.compile(r'\$\{(?P<env_name>[^}^{:]+)(?::(?P<default_value>[^}^{]*))?\}')

# populate env variable matching ${env_var:default_value} in input dictionary
def load_env_vars(config: dict) -> dict:
    # traverse over all keys / subkeys replace env_var recursively
    pass
import re
from functools import lru_cache

def resolve_env_variables(config):
    pattern = re.compile(r"\$\{(\w+):\s*(.*?)\}")  # Match ${ENV_VAR: default_value}
    def resolve_value(value):
        if isinstance(value, str):
            match = pattern.fullmatch(value)
            if match:
                env_var, default_value = match.groups()
                if default_value == 'null':
                    default_value = None
                return os.getenv(env_var, default_value)
        elif isinstance(value, dict):  # Recursively resolve nested dictionaries
            return {k: resolve_value(v) for k, v in value.items()}
        elif isinstance(value, list):  # Recursively resolve lists
            return [resolve_value(v) for v in value]
        return value  # Return unchanged if no match
    return {key: resolve_value(value) for key, value in config.items()}

def main():
    conf_file = Path(__file__).parent.parent / "test" / "env_config.yaml"
    config = config_loader.load_and_merge_configs([conf_file])
    logger.debug(f"config = {config}")
    os.environ['ENV_B'] = 'default_not_used_b'
    env_config = resolve_env_variables(config)
    logger.debug(f"env_config = {json.dumps(env_config)}")

    

if __name__ == "__main__":
    main()