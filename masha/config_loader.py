"""
Module for loading and merging configuration files from various
formats (YAML, JSON, TOML, Properties) into a single dictionary.
"""

import configparser
import json
import logging
import tomllib
from collections.abc import Iterable
from pathlib import Path
from typing import Any

import yaml

from masha.exceptions import ConfigLoadError

logger = logging.getLogger(__name__)

SUPPORTED_SUFFIXES = frozenset(
    {".yaml", ".yml", ".json", ".toml", ".properties"}
)


def _load_properties(file_path: Path) -> dict[str, Any]:
    # Interpolation is disabled so '%' in values is taken literally and
    # cannot reference other keys.
    parser = configparser.ConfigParser(interpolation=None)
    with open(file_path, encoding="utf-8") as f:
        parser.read_file(f)
    return {section: dict(parser[section]) for section in parser.sections()}


def load_config(file_path: Path) -> dict[str, Any]:
    """
    Load configuration from a file based on its extension.

    Args:
        file_path: The path to the configuration file.

    Returns:
        The configuration data. An empty file yields an empty dict.

    Raises:
        ConfigLoadError: If the file is missing, unreadable, malformed, of an
            unsupported type, or its top level is not a mapping.
    """
    suffix = file_path.suffix.lower()
    if suffix not in SUPPORTED_SUFFIXES:
        raise ConfigLoadError(
            f"Unsupported file type: {file_path.suffix} ({file_path})"
        )

    try:
        if suffix in {".yaml", ".yml"}:
            with open(file_path, encoding="utf-8") as f:
                data = yaml.safe_load(f)
        elif suffix == ".json":
            with open(file_path, encoding="utf-8") as f:
                data = json.load(f)
        elif suffix == ".toml":
            with open(file_path, "rb") as f:
                data = tomllib.load(f)
        else:
            data = _load_properties(file_path)
    except FileNotFoundError as e:
        logger.error("Configuration file not found: %s", file_path)
        raise ConfigLoadError(f"File not found: {file_path}") from e
    except (OSError, UnicodeDecodeError) as e:
        logger.error("Cannot read configuration file %s: %s", file_path, e)
        raise ConfigLoadError(f"Cannot read file {file_path}: {e}") from e
    except (
        yaml.YAMLError,
        json.JSONDecodeError,
        tomllib.TOMLDecodeError,
        configparser.Error,
    ) as e:
        logger.error("Malformed configuration file %s: %s", file_path, e)
        raise ConfigLoadError(f"Cannot parse file {file_path}: {e}") from e

    if data is None:
        logger.debug("Configuration file %s is empty", file_path)
        return {}
    if not isinstance(data, dict):
        raise ConfigLoadError(
            f"Top level of {file_path} must be a mapping, "
            f"got {type(data).__name__}"
        )
    logger.debug("Loaded config from %s", file_path)
    return data


def merge_configs(configs: Iterable[dict[str, Any] | None]) -> dict[str, Any]:
    """
    Shallow-merge multiple dictionaries into a new one.

    If there are overlapping top-level keys, the values from later
    dictionaries overwrite those from earlier ones. Inputs are not mutated.

    Args:
        configs: Configuration dictionaries in precedence order (lowest
            first). ``None`` entries are skipped.

    Returns:
        A single merged dictionary.
    """
    merged_config: dict[str, Any] = {}
    for config in configs:
        if config is None:
            continue
        merged_config.update(config)
    logger.debug("Merged %d top-level keys", len(merged_config))
    return merged_config


def load_and_merge_configs(config_paths: Iterable[Path]) -> dict[str, Any]:
    """
    Load and merge multiple configuration files.

    Args:
        config_paths: File paths to the configuration files, in precedence
            order (lowest first).

    Returns:
        The merged configuration.

    Raises:
        ConfigLoadError: If any file cannot be loaded.
    """
    configs = []
    for config_path in config_paths:
        logger.debug("Loading file: %s", config_path)
        configs.append(load_config(Path(config_path)))
    return merge_configs(configs)
