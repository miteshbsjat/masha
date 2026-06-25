"""
Render jinja2 template defined in configuration.
"""

import importlib.util
import logging
from pathlib import Path
from typing import Dict, Optional

import jinja2

from masha.exceptions import TemplateRenderError
from masha.logger_factory import create_logger

logger = create_logger("masha")


def load_functions_from_file(file: str) -> Dict[str, object]:
    """
    Load all Python functions from a given file.

    Args:
        file: The path to the Python file from which to load functions.

    Returns:
        A dictionary containing function names as keys and their
        callable objects as values.
    """
    functions = {}
    if file.endswith(".py"):
        module_name = file[:-3]  # Remove '.py' extension
        spec = importlib.util.spec_from_file_location(module_name, file)
        if spec is None or spec.loader is None:
            return functions
        module = importlib.util.module_from_spec(spec)
        spec.loader.exec_module(module)

        for attr_name in dir(module):
            attr = getattr(module, attr_name)
            if callable(attr) and not attr_name.startswith("_"):
                functions[attr_name] = attr
    return functions


def load_functions_from_directory(directory: str) -> Dict[str, object]:
    """
    Load all Python functions from files in the given directory as Jinja2 filters.

    Args:
        directory: The path to the directory containing Python files with filter functions.

    Returns:
        A dictionary containing filter names as keys and their callable objects as values.
    """
    fxns = {}
    import os

    if os.path.exists(directory):
        for filename in os.listdir(directory):
            file_path = os.path.join(directory, filename)
            if os.path.isfile(file_path):
                fxns.update(load_functions_from_file(file_path))
    return fxns


def render_templates_with_filters(
    input_dict: dict,
    filters_directory: Optional[str] = None,
    tests_directory: Optional[str] = None,
    max_iterations: int = 10,
) -> dict:
    """
    Render templates in a dictionary using Jinja2, applying custom filters and tests.

    Args:
        input_dict: The dictionary containing the template strings to render.
        filters_directory: Path to the directory containing custom filters.
        tests_directory: Path to the directory containing custom tests.
        max_iterations: Maximum number of iterations for rendering.

    Returns:
        The dictionary with rendered template strings.
    """
    env = jinja2.Environment()
    if filters_directory:
        filters = load_functions_from_directory(filters_directory)
        env.filters.update(filters)
    if tests_directory:
        tests = load_functions_from_directory(tests_directory)
        env.tests.update(tests)

    rendered_dict = input_dict.copy()

    def recursive_render(value):
        if isinstance(value, dict):
            return {k: recursive_render(v) for k, v in value.items()}
        if isinstance(value, str):
            template = env.from_string(value)
            return template.render(rendered_dict)
        return value

    for _ in range(max_iterations):
        new_dict = recursive_render(rendered_dict)
        if new_dict == rendered_dict:
            break
        rendered_dict = new_dict
    return rendered_dict
