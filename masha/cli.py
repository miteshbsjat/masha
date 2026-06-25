#!/usr/bin/env python3
"""
Render the input file using Jinja2 with the provided configuration.
"""

import sys
from pathlib import Path
from typing import Any, Dict, Optional

import click
import jinja2
from returns.result import Failure, Result, Success

from masha.config_loader import load_and_merge_configs
from masha.config_validator import load_model_class, validate_config
from masha.env_loader import resolve_env_variables
from masha.exceptions import TemplateRenderError
from masha.logger_factory import create_logger
from masha.template_renderer import (
    load_functions_from_directory,
    render_templates_with_filters,
)


def render_jinja_template(
    input_file: Path,
    output_file: Path,
    config: Dict[str, Any],
    filters_directory: Optional[str] = None,
    tests_directory: Optional[str] = None,
) -> Result[bool, Exception]:
    """
    Render the input file using Jinja2 with the provided configuration.

    Args:
        input_file: The path to the input template file.
        output_file: The path where the rendered output will be saved.
        config: A dictionary containing the configuration for rendering.
        filters_directory: The directory containing custom Jinja2 filters.
        tests_directory: The directory containing custom Jinja2 tests.

    Returns:
        Success(True) if the template is rendered successfully,
        Failure(exception) if an error occurs during rendering.
    """
    try:
        jenv = jinja2.Environment(
            loader=jinja2.FileSystemLoader(input_file.parent)
        )
        if filters_directory:
            filters = load_functions_from_directory(filters_directory)
            jenv.filters.update(filters)
        if tests_directory:
            tests = load_functions_from_directory(tests_directory)
            jenv.tests.update(tests)
        template = jenv.get_template(input_file.name)
        rendered_content = template.render(config)

        with open(output_file, "w", encoding="utf-8") as f:
            f.write(rendered_content)

        logger.info("Rendered output written to %s", output_file)
        return Success(True)
    except jinja2.exceptions.TemplateError as e:
        logger.error("Failed to render template: %s", e)
        return Failure(e)
    except Exception as e:
        logger.error("Unexpected error during template rendering: %s", e)
        return Failure(e)


def process_template_with_validation(
    variables: tuple[Path],
    template_filters_directory: Path,
    template_tests_directory: Path,
    output: Path,
    input_file: Path,
    model_file: Optional[Path] = None,
    class_model: Optional[str] = None,
) -> Result[Dict, Exception]:
    """
    Validate merged configurations against a Pydantic model and render an input template.

    Args:
        variables: A tuple of file paths containing configuration variables.
        template_filters_directory: The directory containing custom template filters.
        template_tests_directory: The directory containing custom template tests.
        output: The path where the rendered template will be saved.
        input_file: The path to the input template file.
        model_file: The path to a Pydantic model file.
        class_model: The name of the model class within the model_file.

    Returns:
        A result object containing either the rendered template configuration
        as a dictionary or an exception if any step fails.
    """
    match load_and_merge_configs(variables):
        case Success(value):
            merged_config = value
        case Failure(value):
            return Failure(
                ValueError(f"Failed to load configs from files: {value}")
            )

    logger.debug("merged_config: %s", merged_config)
    env_config = resolve_env_variables(merged_config)
    logger.debug("env_config: %s", env_config)
    filters_path = template_filters_directory
    tests_path = template_tests_directory
    logger.debug("filters_path: %s", filters_path)
    template_config = render_templates_with_filters(
        env_config, str(filters_path), str(tests_path)
    )
    logger.info("Template config: %s", template_config)

    if model_file and class_model:
        try:
            model_class = load_model_class(model_file, class_model)
            if not model_class:
                return Failure(
                    ValueError("Failed to load the specified model class.")
                )
            validation_result = validate_config(template_config, model_class)
            if isinstance(validation_result, Failure):
                return Failure(
                    ValueError(f"Given config is invalid: {validation_result}")
                )
        except TypeError as e:
            return Failure(ValueError(f"Model type error: {e}"))

    match render_jinja_template(
        input_file,
        output,
        template_config,
        template_filters_directory,
        template_tests_directory,
    ):
        case Failure(value):
            return Failure(ValueError(f"Failed to render template: {value}"))

    return Success(template_config)


@click.command()
@click.option(
    "-v",
    "--variables",
    type=click.Path(exists=True, dir_okay=False, path_type=Path),
    multiple=True,
    required=True,
    help="Path(s) to the various configuration files.",
)
@click.option(
    "-m",
    "--model-file",
    type=click.Path(
        exists=True, file_okay=True, dir_okay=False, path_type=Path
    ),
    required=False,
    default=None,
    help="Path to the Python file containing the Pydantic model class.",
)
@click.option(
    "-c",
    "--class-model",
    type=str,
    required=False,
    default=None,
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
@click.option(
    "-V",
    "--verbose",
    is_flag=True,
    default=False,
    help="Enable debug logging.",
)
@click.argument(
    "input_file",
    type=click.Path(exists=True, dir_okay=False, path_type=Path),
    required=True,
)
def main(
    variables: tuple[Path],
    model_file: Path,
    class_model: str,
    template_filters_directory: Path,
    template_tests_directory: Path,
    output: Path,
    input_file: Path,
    verbose: bool,
):
    """
    Validate merged configurations against a Pydantic model and render an input template.
    """
    global logger
    logger = create_logger("masha", verbose=verbose)

    try:
        match process_template_with_validation(
            variables,
            template_filters_directory,
            template_tests_directory,
            output,
            input_file,
            model_file,
            class_model,
        ):
            case Success(value):
                logger.info("Command run successfully")
                sys.exit(0)
            case Failure(value):
                logger.error("Command failed with error: %s", value)
                click.secho(f"Error: {value}", fg="red", err=True)
                sys.exit(1)
    except Exception as e:
        logger.exception("An unexpected fatal error occurred.")
        click.secho(
            "A fatal unexpected error occurred. Check logs for details.",
            err=True,
            fg="red",
            bold=True,
        )
        sys.exit(1)


if __name__ == "__main__":
    main()
