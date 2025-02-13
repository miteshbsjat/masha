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

import argparse
import configparser
import json
from pathlib import Path
from typing import Any, Dict

import toml
import yaml
from returns.result import Failure, Result, Success

# pylint: disable=W1203
from masha.logger_factory import create_logger

logger = create_logger("masha")


# Function to load configuration files
def load_config(file_path: Path) -> Result[{}, dict]:
    """
    Load configuration from a file based on its extension.

    Args:
        file_path (Path): The path to the configuration file.

    Returns:
        Result: A dictionary containing the configuration data if successful,
                or an error message if the file type is unsupported.
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
            config = configparser.ConfigParser()
            config.read(file_path)
            return Success(
                {
                    section: dict(config[section])
                    for section in config.sections()
                }
            )
        else:
            return Failure(
                {"error": f"Unsupported file type: {file_path.suffix}"}
            )
    except FileNotFoundError as e:
        return Failure({"error": f"File not found: {e}"})


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


def load_and_merge_configs(config_paths: list[Path]) -> Result[Dict, Dict]:
    """
    Load and merge multiple configuration files.

    This function takes a list of file paths to configuration files, loads each one,
    and merges them into a single dictionary. If any file fails to load or merge,
    the function returns an error message.

    Args:
        config_paths (list[Path]): A list of file paths to the configuration files.

    Returns:
        Result[dict, str]: A `Success` containing the merged configuration dictionary
                            if all files are processed successfully.
                           Otherwise, a `Failure` containing an error message indicating
                            which file caused the issue.

    Raises:
        ValueError: If any of the provided file paths are not valid or do not exist.
    """
    configs = []
    for config_path in config_paths:
        logger.debug(f"Loading file: {config_path}")
        match load_config(config_path):
            case Success(config_data):
                configs.append(config_data)
            case Failure(value):
                msg = f"Error processing file {config_path}: {value}"
                logger.warning(msg)
                return Failure({"error": msg})
    merged_config = merge_configs(configs)
    return Success(merged_config)


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
    merged_config = None
    match load_and_merge_configs(args.variables):
        case Success(val):
            merged_config = val
        case Failure(val):
            logger.warning(f"Failed to load config: {val}")
            return

    print(json.dumps(merged_config))


if __name__ == "__main__":
    main()
