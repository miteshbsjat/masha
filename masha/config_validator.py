"""
Validate the configuration against a Pydantic model class.
"""

import logging
from pathlib import Path
from typing import Optional, Type

from pydantic import BaseModel, ValidationError
from returns.result import Failure, Result, Success

from masha.exceptions import ModelValidationError
from masha.logger_factory import create_logger

logger = create_logger("masha")


def validate_config(
    config_data: dict, model_class: Type[BaseModel]
) -> Result[str, str]:
    """
    Validate the configuration data against the provided Pydantic model class.

    Args:
        config_data: A dictionary containing the configuration data to validate.
        model_class: The Pydantic model class defining the expected structure.

    Returns:
        Success(str) with a validation message if valid.
        Failure(str) with error details if invalid.
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


def load_model_class(
    model_file_path: Path, model_class_name: str
) -> Optional[Type[BaseModel]]:
    """
    Load a model class from a specified file path.

    Args:
        model_file_path: The path to the file containing the model class.
        model_class_name: The name of the model class to load.

    Returns:
        The loaded model class if successful, None otherwise.
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
    except (FileNotFoundError, ImportError) as e:
        logger.warning("Failed to load the model class: %s", e)
        return None
    except TypeError:
        raise
    except Exception as e:
        logger.warning("Failed to load the model class: %s", e)
        return None
