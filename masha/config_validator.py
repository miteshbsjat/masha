#!/usr/bin/env python3

import argparse
import yaml
import json
import toml
import configparser
from pathlib import Path
from pydantic import BaseModel, ValidationError, field_validator
from typing import Any, Dict
import config_loader
import env_loader
import template_renderer

# Main validation function
def validate_config(config_data: dict, model_class: BaseModel):
    """
    Validate the configuration data against the provided Pydantic model class.

    Parameters:
    config_data (dict): A dictionary containing the configuration data to be validated.
    model_class (BaseModel): The Pydantic model class that defines the expected structure of the configuration data.

    Returns:
    None

    Raises:
    ValidationError: If the configuration data does not match the expected structure defined by `model_class`.
    """
    try:
        model_instance = model_class(**config_data)
        print(f"Validation successful: {model_instance}")
    except ValidationError as e:
        print("Validation failed with errors:")
        print(e.json())

def load_model_class(model_file_path: Path, model_class_name: str):
    try:
        model_globals = {}
        exec(model_file_path.read_text(), model_globals)
        model_class = model_globals[model_class_name]
        if not issubclass(model_class, BaseModel):
            raise TypeError(f"{model_class_name} is not a subclass of Pydantic BaseModel.")
        return model_class
    except Exception as e:
        print(f"Failed to load the model class: {e}")
        return None

def validate_merged_config(merged_config, model_class):
    try:
        model_class(**merged_config)
        print("Validation successful.")
    except ValidationError as e:
        print(f"Validation failed: {e}")

# CLI entry point
def main():
    parser = argparse.ArgumentParser(description="Validate merged configuration files against a Pydantic model.")
    parser.add_argument("-v", "--variables", nargs='+', type=Path, required=True, help="Paths to the configuration files.")
    parser.add_argument("-m", "--model-file", type=Path, required=True, help="Path to the Python file containing the Pydantic model class.")
    parser.add_argument("-c", "--class-model", type=str, required=True, help="Name of the Pydantic model class to validate against.")

    args = parser.parse_args()

    # Load the model class
    model_class = load_model_class(args.model_file, args.class_model)
    if not model_class:
        return

    # Load and merge all configuration files
    merged_config = config_loader.load_and_merge_configs(args.variables)
            
    if not merged_config:
        return

    print(merged_config)
    env_config = env_loader.resolve_env_variables(merged_config)
    print(env_config)
    filters_path = Path(__file__).parent / "filters"
    print(filters_path)
    temp_config = template_renderer.render_templates_with_filters(env_config, str(filters_path))
    print(temp_config)

    # Validate the merged configuration
    validate_merged_config(env_config, model_class)

if __name__ == "__main__":
    # masha/config_validator.py -v test/config-b.yaml -m test/model.py -c ConfigModel
    main()