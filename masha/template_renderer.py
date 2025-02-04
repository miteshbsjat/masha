#!/usr/bin/env python3

import os
import importlib.util
import jinja2
from pathlib import Path

from logger_factory import create_logger

logger = create_logger("masha")


def load_functions_from_file(file: str):
    """Loads all Python functions from a given file."""
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


def load_filters_from_directory(directory: str):
    """Loads all Python functions from files in the given directory as Jinja2 filters."""
    filters = {}
    if os.path.exists(directory):
        for filename in os.listdir(directory):
            file_path = os.path.join(directory, filename)
            filters.update(load_functions_from_file(file_path))
    return filters


def render_templates_with_filters(
    input_dict: dict, filters_directory: str, max_iterations=10
):
    """
    Renders Jinja2 templates in input_dict using custom filters loaded from filters_directory.
    Resolves dependencies between dictionary values iteratively.

    Args:
        input_dict (dict): Dictionary with Jinja2 templates as values.
        filters_directory (str): Path to the directory containing Python files with filter functions.
        max_iterations (int): Maximum number of iterations to resolve dependencies.

    Returns:
        dict: Dictionary with fully rendered template results.
    """
    filters = load_filters_from_directory(filters_directory)
    env = jinja2.Environment()
    env.filters.update(filters)  # Add custom filters

    rendered_dict = input_dict.copy()

    for _ in range(max_iterations):
        new_dict = {
            key: env.from_string(str(value)).render(rendered_dict)
            for key, value in rendered_dict.items()
        }
        if new_dict == rendered_dict:
            break  # Stop if values don't change
        rendered_dict = new_dict

    return rendered_dict


def main():
    input = {"c": "from {{ b }}", "a": "val_a", "b": "from_{{ a | uppercase }}", "z": 4}
    input = {"name": "test", "version": "0.0.2", "debug": "false", "age": 14}
    logger.debug(f"imput = {input}")
    filters_path = Path(__file__).parent / "filters"
    logger.debug(f"filters_path = {filters_path}")
    rendered = render_templates_with_filters(input, str(filters_path))
    logger.debug(f"rendered = {rendered}")


if __name__ == "__main__":
    main()
