#!/usr/bin/env python3

"""
Module Description:
This module provides functionality to load and merge configuration files from various
formats (YAML, JSON, TOML, Properties) into a single dictionary. It also includes a
command-line interface (CLI) entry point to facilitate loading and merging configurations.

Functions:
- `load_config(file_path: Path) -> dict`: Loads a configuration file into a dictionary
   based on its file extension.
- `merge_configs(configs: Dict[str, Any]) -> dict`: Merges multiple dictionaries into one.
   If there are overlapping keys, the values from later dictionaries will overwrite those from
   earlier ones.
- `load_and_merge_configs(config_paths: list[Path])`: Loads and merges multiple configuration
   files specified by their paths.

CLI Entry Point:
- `main()`: The main function that serves as the entry point for the command-line interface.
   It parses command-line arguments, loads and merges configurations, and prints the merged
   configuration in JSON format.
"""

import json
import configparser
import argparse
from pathlib import Path
from typing import Any, Dict

from logger_factory import create_logger
import toml
import yaml

logger = create_logger("masha")


# Function to load configuration files
def load_config(file_path: Path) -> dict:
    """
    Load configuration file into a dictionary.

    Parameters:
    - file_path (Path): The path to the configuration file.

    Returns:
    - dict: A dictionary containing the configuration data.

    Raises:
    - ValueError: If the file type is not supported.
    """
    if file_path.suffix in {".yaml", ".yml"}:
        with open(file_path, "r", encoding="utf-8") as f:
            return yaml.safe_load(f)
    elif file_path.suffix == ".json":
        with open(file_path, "r", encoding="utf-8") as f:
            return json.load(f)
    elif file_path.suffix == ".toml":
        with open(file_path, "r", encoding="utf-8") as f:
            return toml.load(f)
    elif file_path.suffix == ".properties":
        config = configparser.ConfigParser()
        config.read(file_path)
        return {section: dict(config[section]) for section in config.sections()}
    else:
        raise ValueError(f"Unsupported file type: {file_path.suffix}")


# Function to merge multiple dictionaries
def merge_configs(configs: Dict[str, Any]) -> dict:
    """
    Merge multiple dictionaries into one.

    Parameters:
    configs (Dict[str, Any]): A dictionary where each key is a string representing a
                              configuration name, and the value is another dictionary
                              containing the configuration settings.

    Returns:
    dict: A single dictionary that contains all the configurations from the input
          dictionaries. If there are overlapping keys, the values from later dictionaries
          will overwrite those from earlier ones.
    """
    merged_config = {}
    for config in configs:
        merged_config.update(config)
    logger.debug(f"merged_config = {merged_config}")
    return merged_config


def load_and_merge_configs(config_paths: list[Path]):
    """
    Load and merge multiple configuration files.

    Args:
        config_paths (list[Path]): A list of file paths to the configuration files.

    Returns:
        dict or None: The merged configuration dictionary if successful, otherwise None.
    """
    configs = []
    for config_path in config_paths:
        try:
            logger.debug(f"Loading file: {config_path}")
            config_data = load_config(config_path)
            configs.append(config_data)
        except Exception as e:
            logger.warning(f"Error processing file {config_path}: {e}")
            return None
    merged_config = merge_configs(configs)
    return merged_config


# CLI entry point
def main():
    """
    Validates merged configuration files against a Pydantic model.

    This function sets up an argument parser to accept paths to configuration files.
    It then loads and merges these configuration files, printing the merged result in JSON format.
    """
    parser = argparse.ArgumentParser(
        description="Validate merged configuration files against a Pydantic model."
    )
    parser.add_argument(
        "-v",
        "--variables",
        nargs="+",
        type=Path,
        required=True,
        help="Paths to the configuration files.",
    )

    args = parser.parse_args()

    # # Load the model class
    # model_class = load_model_class(args.model_file, args.class_model)
    # if not model_class:
    #     return

    # Load and merge all configuration files
    merged_config = load_and_merge_configs(args.variables)
    if not merged_config:
        return

    print(json.dumps(merged_config))


if __name__ == "__main__":
    main()
