"""
Import user-supplied Python files (models, Jinja2 filters and tests).

SECURITY: importing a file executes its top-level code with the full
privileges of the current process. Only pass paths the user explicitly
provided on the command line; never derive them from configuration values.
"""

import hashlib
import importlib.util
import logging
import sys
from pathlib import Path
from types import ModuleType

logger = logging.getLogger(__name__)


def _module_name_for(path: Path) -> str:
    # Hash the resolved path so two files with the same stem in different
    # directories never collide in sys.modules.
    digest = hashlib.sha256(str(path).encode("utf-8")).hexdigest()[:12]
    return f"_masha_user_{path.stem}_{digest}"


def import_module_from_path(path: Path) -> ModuleType:
    """
    Import a Python source file as a module.

    Args:
        path: Path to a ``.py`` file.

    Returns:
        The imported module.

    Raises:
        ImportError: If the file is not a ``.py`` file or cannot be imported.
            Exceptions raised by the module's own top-level code are wrapped
            in ImportError with the original as ``__cause__``.
    """
    resolved = path.resolve()
    if resolved.suffix != ".py" or not resolved.is_file():
        raise ImportError(f"Not a Python source file: {path}")

    module_name = _module_name_for(resolved)
    spec = importlib.util.spec_from_file_location(module_name, resolved)
    if spec is None or spec.loader is None:
        raise ImportError(f"Cannot create import spec for {path}")

    module = importlib.util.module_from_spec(spec)
    # Registering before exec lets pydantic/dataclasses resolve the module.
    sys.modules[module_name] = module
    logger.debug("Importing user module %s from %s", module_name, resolved)
    try:
        spec.loader.exec_module(module)
    except Exception as e:  # user code may raise anything
        sys.modules.pop(module_name, None)
        raise ImportError(f"Error while importing {path}: {e}") from e
    return module
