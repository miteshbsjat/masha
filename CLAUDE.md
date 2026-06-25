# MASHA: AI Assistant Guidelines

## 1. Project Context
**MASHA** (MASHup of Configuration Loading) is a Python CLI tool that merges multiple configuration files (YAML, JSON), validates them against a defined Pydantic model, and renders Jinja2 templates for code generation.

### Core Stack
- **CLI Framework**: `click`
- **Validation**: `pydantic`
- **Templating**: `jinja2`
- **Dependency Management**: `poetry`
- **Python Version**: `3.10+`

---

## 2. Python Code Style & Best Practices
- **PEP 8**: Strictly adhere to PEP 8 formatting. Assume the use of `black` for formatting and `isort` for import sorting.
- **Type Hinting**: Provide strict type hints for all function arguments and return types using the `typing` module or Python 3.10+ native generic types (e.g., `list[str]`, `dict[str, Any]`).
- **Docstrings**: Use Google-style docstrings for all modules, classes, and complex functions.
- **Immutability**: Prefer immutable data structures where possible. When passing configuration dictionaries, avoid mutating them unexpectedly.

---

## 3. Logging Best Practices (Strict Enforcement)
Never use `print()` for runtime information, warnings, or errors. All output must go through the standard Python `logging` module or Click's output streams (`click.echo`).

- **Setup & Configuration**: 
  - Configure the root logger in the main CLI entry point.
  - Support a verbose flag (e.g., `-v` or `--debug`) in `click` to toggle log levels between `INFO` and `DEBUG`.
  - Use a standardized format: `%(asctime)s | %(name)s | %(levelname)s | %(message)s`.
- **Lazy Interpolation**: Use the standard logging lazy interpolation rather than f-strings to save evaluation time if the log level is disabled (e.g., `logger.debug("Loaded config from %s", filepath)` instead of `logger.debug(f"Loaded config from {filepath}")`).
- **Level Usage**:
  - `DEBUG`: For tracing execution (e.g., "Merging config dicts", "Loaded template filters").
  - `INFO`: For high-level progress (e.g., "Starting validation", "Rendition complete").
  - `WARNING`: For recoverable anomalies (e.g., "Environment variable expected but not found, falling back to default").
  - `ERROR`: For failures that halt a specific operation.
  - `CRITICAL`: For catastrophic application failures.

---

## 4. Error and Exception Handling (Graceful Execution)
MASHA must fail gracefully. End-users running the CLI should never see a raw Python traceback unless they explicitly run the command in a debug mode.

- **No Naked Excepts**: Never use a bare `except:`. Always catch specific exceptions (e.g., `FileNotFoundError`, `pydantic.ValidationError`, `jinja2.exceptions.TemplateError`).
- **Custom Exceptions**: Define a custom exception hierarchy in an `exceptions.py` module:
  - `MashaBaseError(Exception)`
  - `ConfigLoadError(MashaBaseError)`
  - `ModelValidationError(MashaBaseError)`
  - `TemplateRenderError(MashaBaseError)`
- **CLI Error Handling Boundaries**:
  - Internal functions should raise specific custom exceptions.
  - The topmost `click` command function should wrap the execution in a `try...except` block catching `MashaBaseError`.
  - Upon catching, use `logger.exception("Detailed error log")` to silently log the traceback to a file/debug stream, and use `click.secho(f"Error: {e}", fg="red")` to print a clean, human-readable error to the user before calling `sys.exit(1)`.
- **Resource Management**: ALWAYS use context managers (`with` statements) for file operations (reading configs, writing rendered output) to ensure file handles are closed regardless of exceptions.

### Example Pattern for Graceful Handling:
```python
import logging
import click
from pydantic import ValidationError

logger = logging.getLogger(__name__)

class MashaBaseError(Exception): pass
class ConfigLoadError(MashaBaseError): pass

def load_config(filepath: str) -> dict:
    try:
        with open(filepath, 'r') as f:
            # logic here
            return {}
    except FileNotFoundError as e:
        logger.error("Configuration file not found: %s", filepath)
        raise ConfigLoadError(f"Cannot locate config file: {filepath}") from e

@click.command()
def main():
    try:
        # CLI execution logic
        pass
    except MashaBaseError as e:
        logger.exception("A managed application error occurred.")
        click.secho(f"Execution failed: {str(e)}", err=True, fg="red")
        raise click.Abort()
    except Exception as e:
        logger.exception("An unhandled critical error occurred.")
        click.secho("A fatal unexpected error occurred. Check logs.", err=True, fg="red", bold=True)
        raise click.Abort()

```

## 5. Development & Testing Workflows

* **Package Manager**: Always use `poetry add <package>` or `poetry remove <package>` for dependency management.
* **Running locally**: `poetry run masha <args>`
* **Testing**: Use `pytest`. When writing tests, explicitly test error handling paths by using `pytest.raises(CustomException)` to ensure failures occur gracefully as designed.

