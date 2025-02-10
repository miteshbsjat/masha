#!/usr/bin/env python3
"""
Render the input file using Jinja2 with the provided configuration.
"""

import json
from pathlib import Path
from typing import Any, Dict

import click
import jinja2
from returns.result import Failure, Success

# pylint: disable=W1203
from masha.config_loader import load_and_merge_configs
from masha.config_validator import load_model_class, validate_config
from masha.env_loader import resolve_env_variables
from masha.logger_factory import create_logger
from masha.template_renderer import (
    load_functions_from_directory,
    render_templates_with_filters,
)

logger = create_logger("masha")


def render_template(
    input_file: Path,
    output_file: Path,
    config: Dict[str, Any],
    filters_directory: str = None,
    tests_directory: str = None,
):
    """
    Render the input file using Jinja2 with the provided configuration.

    Args:
        input_file (Path): The path to the input template file.
        output_file (Path): The path where the rendered output will be saved.
        config (Dict[str, Any]): A dictionary containing the configuration for rendering.
        filters_directory (str, optional): The directory containing custom Jinja2 filters.
                            Defaults to None.
        tests_directory (str, optional): The directory containing custom Jinja2 tests.
                            Defaults to None.

    Returns:
        Success: If the template is rendered successfully.
        Failure: If an error occurs during rendering.
    """
    try:
        jenv = jinja2.Environment(
            loader=jinja2.FileSystemLoader(input_file.parent)
        )
        if filters_directory:
            filters = load_functions_from_directory(filters_directory)
            jenv.filters.update(filters)  # Add custom filters fuctions
        if tests_directory:
            tests = load_functions_from_directory(tests_directory)
            jenv.tests.update(tests)  # Add custom tests
        template = jenv.get_template(input_file.name)
        logger.info(template)
        rendered_content = template.render(config)

        with open(output_file, "w", encoding="utf-8") as f:
            f.write(rendered_content)

        logger.info(f"Rendered output written to {output_file}")
    # pylint: disable=W0718
    except Exception as e:
        logger.error(f"Failed to render template: {e}")


# pylint: disable=R0913,R0917,E1120
@click.command()
@click.option(
    "-v",
    "--variables",
    type=click.Path(exists=True, dir_okay=False, path_type=Path),
    multiple=True,
    required=True,
    help="Paths to the various configuration files.",
)
@click.option(
    "-m",
    "--model-file",
    type=click.Path(
        exists=True, file_okay=True, dir_okay=False, path_type=Path
    ),
    required=True,
    help="Path to the Python file containing the Pydantic model class.",
)
@click.option(
    "-c",
    "--class-model",
    type=str,
    required=True,
    help="Name of the Pydantic model class to validate against.",
)
@click.option(
    "-f",
    "--template-filters-directory",
    type=click.Path(
        exists=True, file_okay=False, dir_okay=True, path_type=Path
    ),
    default=None,
    help="Directory containing custom Jinja2 filter functions.",
)
@click.option(
    "-t",
    "--template-tests-directory",
    type=click.Path(
        exists=True, file_okay=False, dir_okay=True, path_type=Path
    ),
    default=None,
    help="Directory containing custom Jinja2 test functions.",
)
@click.option(
    "-o",
    "--output",
    type=click.Path(dir_okay=False, writable=True, path_type=Path),
    required=True,
    help="Path to the output file where the rendered content will be written.",
)
@click.argument(
    "input_file",
    type=click.Path(exists=True, dir_okay=False, path_type=Path),
    required=True,
    # help="Path to the input template file.",
)
def main(
    variables: tuple[Path],
    model_file: Path,
    class_model: str,
    template_filters_directory: Path,
    template_tests_directory: Path,
    output: Path,
    input_file: Path,
):
    """
    Validate merged configurations against a Pydantic model and render an input template.
    """
    # Load the model class
    model_class = load_model_class(model_file, class_model)
    if not model_class:
        click.echo("Failed to load the specified model class.", err=True)
        return

    merged_config = None
    match load_and_merge_configs(variables):
        case Success(value):
            merged_config = value
        case Failure(value):
            logger.warning(f"Failed to load configs from files: {value}")
            return

    logger.debug(f"merged_config: {merged_config}")
    env_config = resolve_env_variables(merged_config)
    logger.debug(f"env_config: {env_config}")
    filters_path = template_filters_directory
    tests_path = template_tests_directory
    logger.debug(f"filters_path: {filters_path}")
    template_config = render_templates_with_filters(
        env_config, str(filters_path), str(tests_path)
    )
    logger.info(json.dumps(template_config))

    # Validate the merged configuration
    validation_result = validate_config(template_config, model_class)
    if isinstance(validation_result, Success):
        logger.info(f"Given config is valid {validation_result}")
    else:
        logger.warning(f"Given config is invalid {validation_result}")
        return

    render_template(
        input_file,
        output,
        template_config,
        template_filters_directory,
        template_tests_directory,
    )


if __name__ == "__main__":
    main()
