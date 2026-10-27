#!/usr/bin/env python3
"""
Command-line entry point: merge configs, validate them, render a template.
"""

import logging
import sys
from collections.abc import Sequence
from pathlib import Path
from typing import Any

import click

from masha.config_loader import load_and_merge_configs
from masha.config_validator import load_model_class, validate_config
from masha.env_loader import resolve_env_variables
from masha.exceptions import MashaBaseError
from masha.logger_factory import configure_logging
from masha.template_renderer import (
    render_template_file,
    render_templates_with_filters,
)
from masha.version import __version__

logger = logging.getLogger(__name__)


def process_template_with_validation(
    variables: Sequence[Path],
    template_filters_directory: Path | None,
    template_tests_directory: Path | None,
    output: Path,
    input_file: Path,
    model_file: Path | None = None,
    class_model: str | None = None,
) -> dict[str, Any]:
    """
    Validate merged configurations against a Pydantic model and render an input template.

    Args:
        variables: File paths containing configuration variables, in
            precedence order (lowest first).
        template_filters_directory: The directory containing custom template filters.
        template_tests_directory: The directory containing custom template tests.
        output: The path where the rendered template will be saved.
        input_file: The path to the input template file.
        model_file: The path to a Pydantic model file.
        class_model: The name of the model class within the model_file.

    Returns:
        The fully resolved configuration used to render the template.

    Raises:
        MashaBaseError: If any stage (load, render, validate, write) fails.
    """
    logger.info("Loading %d configuration file(s)", len(variables))
    merged_config = load_and_merge_configs(variables)
    env_config = resolve_env_variables(merged_config)
    template_config = render_templates_with_filters(
        env_config, template_filters_directory, template_tests_directory
    )
    # Only keys are logged: resolved values may contain secrets.
    logger.debug("Resolved config keys: %s", sorted(template_config))

    if model_file and class_model:
        logger.info("Starting validation against %s", class_model)
        model_class = load_model_class(model_file, class_model)
        validate_config(template_config, model_class)

    render_template_file(
        input_file,
        output,
        template_config,
        template_filters_directory,
        template_tests_directory,
    )
    return template_config


@click.command()
@click.version_option(__version__, prog_name="masha")
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
    help="Enable debug logging (shows tracebacks on failure).",
)
@click.argument(
    "input_file",
    type=click.Path(exists=True, dir_okay=False, path_type=Path),
    required=True,
)
def main(
    variables: tuple[Path, ...],
    model_file: Path | None,
    class_model: str | None,
    template_filters_directory: Path | None,
    template_tests_directory: Path | None,
    output: Path,
    input_file: Path,
    verbose: bool,
) -> None:
    """
    Validate merged configurations against a Pydantic model and render an input template.
    """
    configure_logging(verbose=verbose)

    if bool(model_file) != bool(class_model):
        raise click.UsageError(
            "--model-file and --class-model must be given together."
        )

    try:
        process_template_with_validation(
            variables,
            template_filters_directory,
            template_tests_directory,
            output,
            input_file,
            model_file,
            class_model,
        )
    except MashaBaseError as e:
        # Traceback goes to the debug stream only; users see a clean message.
        logger.debug("A managed application error occurred.", exc_info=True)
        click.secho(f"Error: {e}", err=True, fg="red")
        sys.exit(1)
    except Exception:  # last-resort boundary; never leak a raw traceback
        logger.critical(
            "An unhandled critical error occurred.", exc_info=verbose
        )
        click.secho(
            "A fatal unexpected error occurred. Re-run with --verbose "
            "for details.",
            err=True,
            fg="red",
            bold=True,
        )
        sys.exit(1)
    logger.info("Rendition complete")


if __name__ == "__main__":
    main()
