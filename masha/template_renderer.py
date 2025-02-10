#!/usr/bin/env python3

"""
Render jinja2 template defined in configuration
"""

import importlib.util
import os
from pathlib import Path

import jinja2

# pylint: disable=W1203
from masha.logger_factory import create_logger

logger = create_logger("masha")


def load_functions_from_file(file: str):
    """Loads all Python functions from a given file.

    Args:
        file (str): The path to the Python file from which to load functions.

    Returns:
        dict: A dictionary containing function names as keys and their corresponding
              callable objects as values.
    """
    functions = {}
    if os.path.exists(file) and file.endswith(".py"):
        module_name = file[:-3]  # Remove '.py' extension
        spec = importlib.util.spec_from_file_location(module_name, file)
        module = importlib.util.module_from_spec(spec)
        spec.loader.exec_module(module)

        for attr_name in dir(module):
            attr = getattr(module, attr_name)
            if callable(attr) and not attr_name.startswith(
                "_"
            ):  # Only include functions
                functions[attr_name] = attr
    return functions


def load_functions_from_directory(directory: str):
    """Loads all Python functions from files in the given directory as Jinja2 filters.

    Args:
        directory (str): The path to the directory containing Python files with filter functions.

    Returns:
        dict: A dictionary containing filter names as keys and their corresponding callable
              objects as values.
    """
    fxns = {}
    if os.path.exists(directory):
        for filename in os.listdir(directory):
            file_path = os.path.join(directory, filename)
            fxns.update(load_functions_from_file(file_path))
    return fxns


def render_templates_with_filters(
    input_dict: dict,
    filters_directory: str = None,
    tests_directory: str = None,
    max_iterations=10,
) -> dict:
    """
    Renders templates in a dictionary using Jinja2, applying custom filters and tests.

    Args:
        input_dict (dict): The dictionary containing the template strings to be rendered.
        filters_directory (str, optional): Path to the directory containing custom filters.
                                           Defaults to None.
        tests_directory (str, optional): Path to the directory containing custom tests.
                                         Defaults to None.
        max_iterations (int, optional): Maximum number of iterations for rendering. Defaults to 10.

    Returns:
        dict: The dictionary with rendered template strings.
    """
    env = jinja2.Environment()
    if filters_directory:
        filters = load_functions_from_directory(filters_directory)
        env.filters.update(filters)  # Add custom filters
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


def main():
    """main function to test this module"""
    inp = {
        "c": "from {{ b }}",
        "a": "val_a",
        "b": "from_{{ a | uppercase }}",
        "d": {"e": "{{a}}"},
    }
    # inp = {"name": "test", "version": "0.0.2", "debug": "false", "age": 14}
    logger.debug(f"imput = {inp}")
    filters_path = Path(__file__).parent / "filters"
    logger.debug(f"filters_path = {filters_path}")
    # Path(__file__).parent / "tests"
    rendered = render_templates_with_filters(inp, str(filters_path))
    logger.info(f"rendered = {rendered}")


if __name__ == "__main__":
    main()
