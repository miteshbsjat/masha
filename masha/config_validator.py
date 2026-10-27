"""
Validate the configuration against a Pydantic model class.
"""

import logging
from collections.abc import Mapping
from pathlib import Path
from typing import Any

from pydantic import BaseModel, ValidationError

from masha.exceptions import ModelValidationError
from masha.module_loader import import_module_from_path

logger = logging.getLogger(__name__)


def validate_config(
    config_data: Mapping[str, Any], model_class: type[BaseModel]
) -> BaseModel:
    """
    Validate the configuration data against the provided Pydantic model class.

    Args:
        config_data: The configuration data to validate.
        model_class: The Pydantic model class defining the expected structure.

    Returns:
        The validated model instance.

    Raises:
        ModelValidationError: If the configuration does not match the model.
    """
    try:
        model_instance = model_class.model_validate(dict(config_data))
    except ValidationError as e:
        logger.warning(
            "Validation against %s failed with %d error(s)",
            model_class.__name__,
            e.error_count(),
        )
        raise ModelValidationError(
            f"Configuration is invalid for {model_class.__name__}: {e}"
        ) from e
    logger.debug("Validation against %s successful", model_class.__name__)
    return model_instance


def load_model_class(
    model_file_path: Path, model_class_name: str
) -> type[BaseModel]:
    """
    Load a Pydantic model class from a Python file.

    SECURITY: the model file is imported, which executes its code. Only load
    model files from trusted locations.

    Args:
        model_file_path: The path to the file containing the model class.
        model_class_name: The name of the model class to load.

    Returns:
        The loaded model class.

    Raises:
        ModelValidationError: If the file cannot be imported, the class is
            missing, or it is not a subclass of ``pydantic.BaseModel``.
    """
    try:
        module = import_module_from_path(Path(model_file_path))
    except ImportError as e:
        logger.error("Failed to import model file %s", model_file_path)
        raise ModelValidationError(
            f"Cannot load model file {model_file_path}: {e}"
        ) from e

    model_class = getattr(module, model_class_name, None)
    if model_class is None:
        raise ModelValidationError(
            f"Class {model_class_name!r} not found in {model_file_path}"
        )
    if not (
        isinstance(model_class, type) and issubclass(model_class, BaseModel)
    ):
        raise ModelValidationError(
            f"{model_class_name} is not a subclass of pydantic.BaseModel"
        )
    return model_class
