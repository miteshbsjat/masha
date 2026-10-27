"""
Render Jinja2 templates embedded in configuration and template files.

All rendering uses :class:`jinja2.sandbox.SandboxedEnvironment` so that
template expressions cannot reach Python internals (``__class__``,
``__globals__``, ...), which blocks server-side template injection through
configuration values.
"""

import inspect
import logging
from collections.abc import Callable
from pathlib import Path
from typing import Any

import jinja2
from jinja2.exceptions import SecurityError
from jinja2.sandbox import SandboxedEnvironment

from masha.exceptions import PluginLoadError, TemplateRenderError
from masha.module_loader import import_module_from_path

logger = logging.getLogger(__name__)

# Autoescape only markup outputs; code-generation targets (yaml, sh, py, ...)
# must be emitted verbatim.
_AUTOESCAPE_EXTENSIONS = ("html", "htm", "xml", "html.j2", "htm.j2", "xml.j2")


class StrictSandboxedEnvironment(SandboxedEnvironment):
    """
    Sandbox that raises on unsafe attribute access.

    The stock sandbox returns an undefined value that silently renders as an
    empty string; raising instead makes injection attempts visible.
    """

    def unsafe_undefined(self, obj: Any, attribute: str) -> Any:
        raise SecurityError(
            f"Access to attribute {attribute!r} of "
            f"{type(obj).__name__!r} object is unsafe"
        )


def load_functions_from_file(
    file: str | Path,
) -> dict[str, Callable[..., Any]]:
    """
    Load the public functions defined in a Python file.

    Only functions defined in the file itself are returned; names starting
    with ``_`` and objects imported from other modules are ignored.

    SECURITY: the file is imported, which executes its code.

    Args:
        file: The path to the Python file from which to load functions.

    Returns:
        A mapping of function names to function objects. Non-``.py`` files
        yield an empty mapping.

    Raises:
        PluginLoadError: If the file cannot be imported.
    """
    path = Path(file)
    if path.suffix != ".py":
        return {}
    try:
        module = import_module_from_path(path)
    except ImportError as e:
        logger.error("Failed to load functions from %s", path)
        raise PluginLoadError(str(e)) from e

    functions: dict[str, Callable[..., Any]] = {
        name: obj
        for name, obj in inspect.getmembers(module, inspect.isfunction)
        if not name.startswith("_") and obj.__module__ == module.__name__
    }
    logger.debug("Loaded %s from %s", sorted(functions), path)
    return functions


def load_functions_from_directory(
    directory: str | Path,
) -> dict[str, Callable[..., Any]]:
    """
    Load the public functions of every ``.py`` file in a directory.

    Files are processed in sorted order so that, when two files define the
    same name, the result is deterministic (the later file wins).

    Args:
        directory: The directory containing Python files with functions.

    Returns:
        A mapping of function names to function objects.

    Raises:
        PluginLoadError: If the directory does not exist or a file cannot be
            imported.
    """
    path = Path(directory)
    if not path.is_dir():
        raise PluginLoadError(f"Not a directory: {path}")

    functions: dict[str, Callable[..., Any]] = {}
    for file_path in sorted(path.glob("*.py")):
        if file_path.is_file():
            functions.update(load_functions_from_file(file_path))
    return functions


def create_environment(
    filters_directory: str | Path | None = None,
    tests_directory: str | Path | None = None,
    loader: jinja2.BaseLoader | None = None,
) -> StrictSandboxedEnvironment:
    """
    Create a sandboxed Jinja2 environment with custom filters and tests.

    Args:
        filters_directory: Directory containing custom filter functions.
        tests_directory: Directory containing custom test functions.
        loader: Optional template loader for file-based templates.

    Returns:
        The configured environment.

    Raises:
        PluginLoadError: If filters or tests cannot be loaded.
    """
    env = StrictSandboxedEnvironment(
        loader=loader,
        autoescape=jinja2.select_autoescape(
            enabled_extensions=_AUTOESCAPE_EXTENSIONS,
            default_for_string=False,
            default=False,
        ),
    )
    if filters_directory:
        env.filters.update(load_functions_from_directory(filters_directory))
    if tests_directory:
        env.tests.update(load_functions_from_directory(tests_directory))
    return env


def render_templates_with_filters(
    input_dict: dict[str, Any],
    filters_directory: str | Path | None = None,
    tests_directory: str | Path | None = None,
    max_iterations: int = 10,
) -> dict[str, Any]:
    """
    Render templates in a dictionary using Jinja2, applying custom filters and tests.

    String values are rendered repeatedly against the dictionary itself until
    the result stops changing, so values may reference other values.

    Args:
        input_dict: The dictionary containing the template strings to render.
            It is not mutated.
        filters_directory: Path to the directory containing custom filters.
        tests_directory: Path to the directory containing custom tests.
        max_iterations: Maximum number of iterations for rendering.

    Returns:
        A new dictionary with rendered template strings.

    Raises:
        PluginLoadError: If filters or tests cannot be loaded.
        TemplateRenderError: If a value is not a valid template, fails to
            render, or attempts an operation blocked by the sandbox.
    """
    env = create_environment(filters_directory, tests_directory)
    rendered_dict = dict(input_dict)

    def recursive_render(value: Any) -> Any:
        if isinstance(value, dict):
            return {k: recursive_render(v) for k, v in value.items()}
        if isinstance(value, str):
            return env.from_string(value).render(rendered_dict)
        return value

    try:
        for _ in range(max_iterations):
            new_dict = recursive_render(rendered_dict)
            if new_dict == rendered_dict:
                break
            rendered_dict = new_dict
        else:
            logger.warning(
                "Config templates did not converge after %d iterations; "
                "check for self-referencing values",
                max_iterations,
            )
    except jinja2.TemplateError as e:
        logger.error("Failed to render config templates: %s", e)
        raise TemplateRenderError(
            f"Failed to render configuration templates: {e}"
        ) from e
    return rendered_dict


def render_template_file(
    input_file: Path,
    output_file: Path,
    config: dict[str, Any],
    filters_directory: str | Path | None = None,
    tests_directory: str | Path | None = None,
) -> None:
    """
    Render a Jinja2 template file with the given configuration.

    The template is fully rendered in memory before the output file is
    opened, so a rendering failure never leaves a truncated output file.

    Args:
        input_file: The path to the input template file.
        output_file: The path where the rendered output will be saved.
        config: The configuration used as the template context.
        filters_directory: Directory containing custom filter functions.
        tests_directory: Directory containing custom test functions.

    Raises:
        PluginLoadError: If filters or tests cannot be loaded.
        TemplateRenderError: If the template cannot be rendered or the
            output cannot be written.
    """
    env = create_environment(
        filters_directory,
        tests_directory,
        loader=jinja2.FileSystemLoader(input_file.parent),
    )
    try:
        rendered_content = env.get_template(input_file.name).render(config)
    except jinja2.TemplateError as e:
        logger.error("Failed to render template %s: %s", input_file, e)
        raise TemplateRenderError(
            f"Failed to render template {input_file}: {e}"
        ) from e

    try:
        with open(output_file, "w", encoding="utf-8") as f:
            f.write(rendered_content)
    except OSError as e:
        logger.error("Cannot write output file %s: %s", output_file, e)
        raise TemplateRenderError(
            f"Cannot write output file {output_file}: {e}"
        ) from e
    logger.info("Rendered output written to %s", output_file)
