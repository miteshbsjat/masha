#!/usr/bin/env python3
"""
Validate the configuration against pydantic Model class
"""

import argparse
from pathlib import Path

from pydantic import BaseModel, ValidationError
from returns.result import Failure, Result, Success

# pylint: disable=W1203
from masha.config_loader import load_and_merge_configs
from masha.env_loader import resolve_env_variables
from masha.logger_factory import create_logger
from masha.template_renderer import render_templates_with_filters

logger = create_logger("masha")


# Main validation function
def validate_config(
    config_data: dict, model_class: BaseModel
) -> Result[str, str]:
    """
    Validate the configuration data against the provided Pydantic model class.

    Parameters:
    config_data (dict): A dictionary containing the configuration data to be validated.
    model_class (BaseModel): The Pydantic model class that defines the expected structure of
    the configuration data.

    Returns:
    None

    Raises:
    ValidationError: If the configuration data does not match the expected structure defined
    by `model_class`.
    """
    try:
        model_instance = model_class(**config_data)
        msg = f"Validation successful: {model_instance}"
        logger.debug(msg)
        return Success(msg)
    except ValidationError as e:
        msg = f"Validation failed with errors: {e}"
        logger.warning(msg)
        return Failure(msg)


# pylint: disable=W0122,W0718
def load_model_class(model_file_path: Path, model_class_name: str):
    """
    Load a model class from a specified file path.

    Args:
        model_file_path (Path): The path to the file containing the model class.
        model_class_name (str): The name of the model class to load.

    Returns:
        Optional[Type]: The loaded model class if successful, otherwise None.

    Raises:
        TypeError: If the specified class is not a subclass of Pydantic BaseModel.

    Notes:
        - This function reads the content of the file at `model_file_path` and executes it in a
            local namespace.
        - It then attempts to retrieve the class named `model_class_name` from this namespace.
        - If the retrieved class is not a subclass of `BaseModel`, a `TypeError` is raised.
        - Any exceptions encountered during the execution or retrieval process are logged as
            warnings.

    Example:
        >>> model_file_path = Path("path/to/model.py")
        >>> model_class_name = "MyModel"
        >>> MyModelClass = load_model_class(model_file_path, model_class_name)
        >>> if MyModelClass is not None:
        ...     print(f"Model class {model_class_name} loaded successfully.")
    """
    try:
        model_globals = {}
        exec(model_file_path.read_text(), model_globals)
        model_class = model_globals[model_class_name]
        if not issubclass(model_class, BaseModel):
            raise TypeError(
                f"{model_class_name} is not a subclass of Pydantic BaseModel."
            )
        return model_class
    except Exception as e:
        logger.warning(f"Failed to load the model class: {e}")
        return None


# CLI entry point
def main():
    """
    test config validation
    """
    parser = argparse.ArgumentParser(
        description="Validate merged configurations against a Pydantic model."
    )
    parser.add_argument(
        "-v",
        "--variables",
        type=Path,
        nargs="+",
        required=True,
        help="Paths to the various configuration files.",
    )
    parser.add_argument(
        "-m",
        "--model-file",
        type=Path,
        required=True,
        help="Path to the Python file containing the Pydantic model class.",
    )
    parser.add_argument(
        "-c",
        "--class-model",
        type=str,
        required=True,
        help="Name of the Pydantic model class to validate against.",
    )

    args = parser.parse_args()

    # Load the model class
    model_class = load_model_class(args.model_file, args.class_model)
    if not model_class:
        return

    # Load and merge all configuration files
    merged_config = None
    match load_and_merge_configs(args.variables):
        case Success(value):
            merged_config = value
        case Failure(value):
            logger.warning(f"Failed to load configs: {value}")
            return

    logger.info(merged_config)
    env_config = resolve_env_variables(merged_config)
    logger.info(env_config)
    filters_path = Path(__file__).parent / "filters"
    logger.debug(filters_path)
    temp_config = render_templates_with_filters(env_config, str(filters_path))
    logger.info(temp_config)

    # Validate the merged configuration
    # validate_merged_config(env_config, model_class)
    validation_result = validate_config(temp_config, model_class)
    if isinstance(validation_result, Success):
        logger.info(f"Given config is valid {validation_result}")
    else:
        logger.warning(f"Given config is invalid {validation_result}")


if __name__ == "__main__":
    # masha/config_validator.py -v test/config-b.yaml -m test/model.py -c ConfigModel
    main()
