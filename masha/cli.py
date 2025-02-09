#!/usr/bin/env python3

from pathlib import Path
from pydantic import BaseModel, ValidationError
from returns.result import Result, Success, Failure
from typing import Any, Dict
import click
import jinja2
import json

# pylint: disable=E0401
import config_loader
import env_loader
import template_renderer
import config_validator

from logger_factory import create_logger

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
    """
    try:
        env = jinja2.Environment(loader=jinja2.FileSystemLoader(input_file.parent))
        if filters_directory:
            filters = template_renderer.load_functions_from_directory(filters_directory)
            env.filters.update(filters)  # Add custom filters
        if tests_directory:
            tests = template_renderer.load_functions_from_directory(tests_directory)
            env.tests.update(tests)
        template = env.get_template(input_file.name)
        logger.info(template)
        rendered_content = template.render(config)

        with open(output_file, "w", encoding="utf-8") as f:
            f.write(rendered_content)

        logger.info(f"Rendered output written to {output_file}")
    except Exception as e:
        logger.error(f"Failed to render template: {e}")


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
    type=click.Path(exists=True, file_okay=True, dir_okay=False, path_type=Path),
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
    "--template-functions-directory",
    type=click.Path(exists=True, file_okay=False, dir_okay=True, path_type=Path),
    default=None,
    help="Directory containing custom Jinja2 filter functions.",
)
@click.option(
    "-t",
    "--template-tests-directory",
    type=click.Path(exists=True, file_okay=False, dir_okay=True, path_type=Path),
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
    'input_file',
    type=click.Path(exists=True, dir_okay=False, path_type=Path),
    required=True,
    # help="Path to the input template file.",
)
def main(
    variables: tuple[Path],
    model_file: Path, 
    class_model: str, 
    template_functions_directory: Path, 
    template_tests_directory: Path, 
    output: Path, 
    input_file: Path
):
    """
    Validate merged configurations against a Pydantic model and render an input template.
    """
    # Load the model class
    model_class = config_validator.load_model_class(model_file, class_model)
    if not model_class:
        click.echo("Failed to load the specified model class.", err=True)
        return

    merged_config = None
    match config_loader.load_and_merge_configs(variables):
        case Success(value):
            merged_config = value
        case Failure(value):
            logger.warning(f"Failed to load configs: {value}")
            return
    
    logger.info(merged_config)
    env_config = env_loader.resolve_env_variables(merged_config)
    logger.info(env_config)
    filters_path = template_functions_directory
    tests_path = template_tests_directory
    logger.debug(filters_path)
    temp_config = template_renderer.render_templates_with_filters(
        env_config, str(filters_path), str(tests_path)
    )
    logger.info(json.dumps(temp_config))

    # Validate the merged configuration
    validation_result = config_validator.validate_config(temp_config, model_class)
    if isinstance(validation_result, Success):
        logger.info(f"Given config is valid {validation_result}")
    else:
        logger.warning(f"Given config is invalid {validation_result}")
        return

    render_template(input_file, output, temp_config, template_functions_directory, template_tests_directory)

    


if __name__ == "__main__":
    main()
