"""
Module for loading and merging configuration files from various
formats (YAML, JSON, TOML, Properties) into a single dictionary.
"""

import json
import logging
from pathlib import Path
from typing import Any, Dict, List

import toml
import yaml
from returns.result import Failure, Result, Success

from masha.exceptions import ConfigLoadError
from masha.logger_factory import create_logger

logger = create_logger("masha")


def load_config(file_path: Path) -> Result[None, dict]:
    """
    Load configuration from a file based on its extension.

    Args:
        file_path: The path to the configuration file.

    Returns:
        Success(dict) with the configuration data if successful,
        Failure(dict) with an error message if the file type is unsupported
        or the file is not found.
    """
    try:
        if file_path.suffix in {".yaml", ".yml"}:
            with open(file_path, "r", encoding="utf-8") as f:
                return Success(yaml.safe_load(f))
        elif file_path.suffix == ".json":
            with open(file_path, "r", encoding="utf-8") as f:
                return Success(json.load(f))
        elif file_path.suffix == ".toml":
            with open(file_path, "r", encoding="utf-8") as f:
                return Success(toml.load(f))
        elif file_path.suffix == ".properties":
            import configparser

            config = configparser.ConfigParser()
            config.read(file_path)
            return Success(
                {section: dict(config[section]) for section in config.sections()}
            )
        else:
            return Failure(
                {"error": f"Unsupported file type: {file_path.suffix}"}
            )
    except FileNotFoundError as e:
        msg = f"File not found: {e}"
        logger.error(msg)
        return Failure({"error": msg})


def merge_configs(configs: Dict[str, Any]) -> dict:
    """
    Merge multiple dictionaries into one.

    If there are overlapping keys, the values from later dictionaries
    will overwrite those from earlier ones.

    Args:
        configs: A dictionary where each key is a configuration name and
                 the value is a dictionary of settings.

    Returns:
        A single merged dictionary.
    """
    merged_config = {}
    for config in configs:
        if config is None:
            continue
        merged_config.update(config)
    logger.debug("merged_config: %s", merged_config)
    return merged_config


def load_and_merge_configs(config_paths: List[Path]) -> Result[Dict, Dict]:
    """
    Load and merge multiple configuration files.

    Args:
        config_paths: A list of file paths to the configuration files.

    Returns:
        Success(dict) with the merged configuration if all files process
        successfully. Failure(dict) with an error message indicating which
        file caused the issue.
    """
    configs = []
    for config_path in config_paths:
        logger.debug("Loading file: %s", config_path)
        match load_config(config_path):
            case Success(config_data):
                configs.append(config_data)
            case Failure(value):
                msg = f"Error processing file {config_path}: {value}"
                logger.warning(msg)
                return Failure({"error": msg})
    merged_config = merge_configs(configs)
    return Success(merged_config)
