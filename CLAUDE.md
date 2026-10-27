# MASHA: AI Assistant Guidelines

## 1. Project Context
**MASHA** (MASHup of Configuration Loading) is a Python CLI tool that merges multiple configuration files (YAML, JSON, TOML, `.properties`), resolves `${ENV_VAR:default}` placeholders, renders Jinja2 expressions inside config values, validates the result against a user-supplied Pydantic model, and renders a Jinja2 template for code generation.

### Core Stack
- **CLI Framework**: `click`
- **Validation**: `pydantic` v2
- **Templating**: `jinja2` (always via the sandbox, see §6)
- **Parsing**: `pyyaml` (`safe_load` only), stdlib `json`, `tomllib`, `configparser`
- **Dependency Management**: `poetry`
- **Python Version**: `3.13+` (see `pyproject.toml` / `.tool-versions`)

### Module Map
| Module | Responsibility |
| --- | --- |
| `masha/cli.py` | Click entry point; the **only** place that configures logging and catches errors for the user. |
| `masha/config_loader.py` | Load one file per format; shallow-merge in precedence order. Raises `ConfigLoadError`. |
| `masha/env_loader.py` | Resolve `${VAR:default}` placeholders (pure, non-mutating). |
| `masha/template_renderer.py` | Sandboxed Jinja2 env, filter/test loading, config-value and file rendering. Raises `TemplateRenderError` / `PluginLoadError`. |
| `masha/config_validator.py` | Load the Pydantic model class and validate. Raises `ModelValidationError`. |
| `masha/module_loader.py` | The single place that imports user-supplied `.py` files. |
| `masha/logger_factory.py` | `configure_logging(verbose)` for the CLI. |
| `masha/exceptions.py` | Custom exception hierarchy. |

---

## 2. Python Code Style & Best Practices
- **PEP 8**: Formatted with `black` (line length 79), imports sorted by `isort` (`profile = "black"`), linted with `ruff` (rules configured in `pyproject.toml`). Run `make format` before committing.
- **Type Hinting**: Strict type hints on every function, checked with `mypy --strict` (`make typecheck`). Use native generics and unions (`list[str]`, `dict[str, Any]`, `Path | None`); import abstract types from `collections.abc` (`Iterable`, `Mapping`, `Callable`, `Sequence`). Do not use `typing.Dict`, `List`, `Optional`, `Type`.
- **Docstrings**: Google-style docstrings for all modules, public classes and functions, including a `Raises:` section listing the custom exceptions a function can raise.
- **Immutability**: Never mutate caller-supplied config dicts. Functions return new structures (`dict(...)`, comprehensions). Tests assert inputs are unchanged.
- **Paths**: Use `pathlib.Path`, not `os.path`. Accept `str | Path` at public boundaries and convert with `Path(...)`.
- **Imports**: Top-level imports only (no imports inside functions) unless breaking a cycle. No `sys.path` manipulation anywhere, including tests — import from the `masha` package.
- **Determinism**: When iterating the filesystem, sort results (`sorted(path.glob("*.py"))`) so output does not depend on directory order.
- **Public API**: Everything re-exported from `masha/__init__.py` is public; keep `__all__` in sync when adding or removing functions.

---

## 3. Logging Best Practices (Strict Enforcement)
Never use `print()` for runtime information, warnings, or errors. All output must go through the standard Python `logging` module or Click's output streams (`click.echo` / `click.secho`).

- **Setup & Configuration**:
  - Library modules declare `logger = logging.getLogger(__name__)` and **never** configure handlers, levels or call `basicConfig`/`fileConfig`. Importing `masha` must not change the host application's logging.
  - Only `masha/cli.py` calls `configure_logging(verbose=...)` from `masha.logger_factory`.
  - The `-V` / `--verbose` flag toggles `INFO` ↔ `DEBUG` (`-v` is taken by `--variables`).
  - Logs go to **stderr** so they never mix with rendered output.
  - Standard format: `%(asctime)s | %(name)s | %(levelname)s | %(message)s`.
- **Lazy Interpolation**: Use `logger.debug("Loaded config from %s", filepath)`, never f-strings or `%`/`.format()` inside the log call (enforced by ruff `G` rules).
- **Never log secrets**: Config values may contain credentials resolved from environment variables. Log **keys, counts and file paths**, never resolved values or whole config dicts — not even at DEBUG.
- **Level Usage**:
  - `DEBUG`: Tracing execution (e.g., "Merged 7 top-level keys", "Loaded filters from …", managed-error tracebacks).
  - `INFO`: High-level progress (e.g., "Starting validation", "Rendition complete").
  - `WARNING`: Recoverable anomalies (e.g., config templates did not converge).
  - `ERROR`: Failures that halt a specific operation (logged where the custom exception is raised).
  - `CRITICAL`: Catastrophic, unexpected application failures.

---

## 4. Error and Exception Handling (Graceful Execution)
MASHA must fail gracefully. End-users running the CLI should never see a raw Python traceback unless they explicitly run with `--verbose`.

- **No Naked or Blind Excepts**: Never use a bare `except:`. Catch specific exceptions (`FileNotFoundError`, `OSError`, `yaml.YAMLError`, `json.JSONDecodeError`, `tomllib.TOMLDecodeError`, `pydantic.ValidationError`, `jinja2.TemplateError`, …). `except Exception` is allowed only at two boundaries, each with a comment: the CLI's last-resort handler and `module_loader` wrapping errors raised by user code.
- **Custom Exceptions** (`masha/exceptions.py`):
  - `MashaBaseError(Exception)`
  - `ConfigLoadError(MashaBaseError)` — missing, unreadable, malformed, unsupported or non-mapping config files.
  - `ModelValidationError(MashaBaseError)` — model file/class problems and Pydantic validation failures.
  - `TemplateRenderError(MashaBaseError)` — Jinja2 syntax/runtime/sandbox errors and output write failures.
  - `PluginLoadError(MashaBaseError)` — custom filter/test files that cannot be loaded.
- **Raise, don't return errors**: Internal functions raise custom exceptions and return plain values. Do not return sentinel `None`, error dicts, or `Result` objects. Always chain with `raise ... from e`.
- **CLI Error Handling Boundaries**:
  - Argument combinations Click cannot express (e.g. `--model-file` without `--class-model`) raise `click.UsageError` (exit code 2).
  - `main()` wraps execution in `try...except MashaBaseError`, logs the traceback at DEBUG (`logger.debug(..., exc_info=True)`), prints `click.secho(f"Error: {e}", err=True, fg="red")` and exits with code 1.
  - A final `except Exception` logs at CRITICAL (traceback only when verbose), prints a generic message and exits with code 1.
- **Resource Management**: ALWAYS use context managers (`with` statements) for file operations, always pass `encoding="utf-8"` for text files (binary mode for `tomllib`).
- **No partial output**: Render fully in memory before opening the output file.

### Example Pattern for Graceful Handling:
```python
import json
import logging
import sys
from pathlib import Path
from typing import Any

import click

from masha.exceptions import ConfigLoadError, MashaBaseError
from masha.logger_factory import configure_logging

logger = logging.getLogger(__name__)


def load_config(filepath: Path) -> dict[str, Any]:
    try:
        with open(filepath, encoding="utf-8") as f:
            return json.load(f)
    except FileNotFoundError as e:
        logger.error("Configuration file not found: %s", filepath)
        raise ConfigLoadError(f"File not found: {filepath}") from e


@click.command()
@click.option("-V", "--verbose", is_flag=True)
def main(verbose: bool) -> None:
    configure_logging(verbose=verbose)
    try:
        ...
    except MashaBaseError as e:
        logger.debug("A managed application error occurred.", exc_info=True)
        click.secho(f"Error: {e}", err=True, fg="red")
        sys.exit(1)
    except Exception:  # last-resort boundary; never leak a raw traceback
        logger.critical("An unhandled critical error occurred.", exc_info=verbose)
        click.secho("A fatal unexpected error occurred. Re-run with --verbose "
                    "for details.", err=True, fg="red", bold=True)
        sys.exit(1)
```

---

## 5. Development & Testing Workflows

* **Package Manager**: Always use `poetry add <package>` / `poetry remove <package>` (`--group dev` for tooling). Never edit dependency tables by hand. Runtime deps go in `[tool.poetry.dependencies]`; test/lint tools in the dev group only.
* **Running locally**: `poetry run masha <args>`
* **Make targets**:
  - `make format` — isort, black, ruff `--fix`.
  - `make lint` — isort/black in check mode + ruff.
  - `make typecheck` — mypy strict.
  - `make security` — bandit + pip-audit.
  - `make test` — pytest with coverage.
  - `make check` — all of the above; must pass before a change is considered done.
* **Testing**: Use `pytest` (tests live in `test/`).
  - Explicitly test error paths with `pytest.raises(CustomException, match=...)`.
  - Use `tmp_path` for generated files and `monkeypatch.setenv/delenv` for environment variables — never mutate `os.environ` directly.
  - Test the CLI with `click.testing.CliRunner`, asserting exit codes and that `"Traceback"` never appears in output.
  - Every security control in §6 has a regression test; keep it that way when changing related code.
  - Coverage is measured with branches and must stay ≥ 95% (`fail_under` in `pyproject.toml`; currently 100%). New code ships with tests for both the happy path and every `raise`.
  - `test/conftest.py` resets the `masha` logger after each test (the CLI disables propagation and binds a handler to `CliRunner`'s stderr). Use `caplog.at_level(..., logger="masha")` to assert on log output — e.g. that secrets are never logged.
  - Test one file per module (`test/test_<module>.py`). Don't import a name starting with `test_` from `masha/tests/` directly; pytest would collect it as a test. Import the module instead.

---

## 6. Security Practices (Strict Enforcement)

MASHA processes configuration that may come from many sources and imports user Python code. Treat **config file contents as untrusted data** and **CLI-supplied code paths as trusted-by-the-user code**.

- **Deserialization**:
  - YAML: `yaml.safe_load` only. Never `yaml.load`, `yaml.unsafe_load` or `yaml.FullLoader`.
  - `.properties`: `configparser.ConfigParser(interpolation=None)`.
  - Never use `pickle`, `marshal`, `shelve` or `eval` on config data.
  - The top level of every config file must be a mapping; reject anything else.
- **Template rendering**:
  - Always create environments via `template_renderer.create_environment()`, which returns `StrictSandboxedEnvironment` (a `SandboxedEnvironment` that *raises* `SecurityError` on unsafe attribute access instead of rendering an empty string). Never instantiate `jinja2.Environment` or `jinja2.Template` directly.
  - Autoescape is enabled only for `.html`, `.htm`, `.xml` (and their `.j2` variants); code-generation outputs stay unescaped by design. Do not disable this selectively.
  - Keep `Jinja2 >= 3.1.6` (sandbox-escape fixes).
- **Executing user code**:
  - `--model-file`, `--template-filters-directory` and `--template-tests-directory` import Python files and therefore execute them. All such imports go through `masha/module_loader.import_module_from_path()`; no `exec`, `eval`, `compile` or ad-hoc `importlib` elsewhere.
  - Never derive a path to import from config values or environment variables — only from explicit CLI arguments.
  - Only functions *defined in* a filter/test file (public, not imported from elsewhere) are registered.
- **Secrets**: Never log, echo or include resolved config values in exception messages. Pydantic `ValidationError` text is acceptable in user-facing errors (it is the user's own data), but never log it at INFO or above along with the full config.
- **Subprocesses & shell**: Do not add `subprocess`, `os.system` or `shell=True`. If ever required, pass argument lists, never interpolated strings.
- **Filesystem**: Open files with explicit modes and encodings; never `chmod` or follow paths from config values for writing. Output is written only to the `--output` path.
- **Dependencies**: Use caret ranges (not exact pins) for runtime deps so security patches are picked up. Run `make security` after any dependency change; `pip-audit` must report no known vulnerabilities and `bandit` no findings. Ruff's `S` (bandit) rules are enabled — do not add `# noqa: S...` without a comment explaining why it is safe.
