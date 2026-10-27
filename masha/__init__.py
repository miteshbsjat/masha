"""
MASHA: merge configuration files, validate them and render Jinja2 templates.
"""

from .config_loader import load_and_merge_configs, load_config, merge_configs
from .config_validator import load_model_class, validate_config
from .env_loader import resolve_env_variables
from .exceptions import (
    ConfigLoadError,
    MashaBaseError,
    ModelValidationError,
    PluginLoadError,
    TemplateRenderError,
)
from .logger_factory import configure_logging, create_logger
from .template_renderer import (
    create_environment,
    load_functions_from_directory,
    load_functions_from_file,
    render_template_file,
    render_templates_with_filters,
)
from .version import __version__

__all__ = (
    "ConfigLoadError",
    "MashaBaseError",
    "ModelValidationError",
    "PluginLoadError",
    "TemplateRenderError",
    "configure_logging",
    "create_environment",
    "create_logger",
    "load_and_merge_configs",
    "load_config",
    "load_functions_from_directory",
    "load_functions_from_file",
    "load_model_class",
    "merge_configs",
    "render_template_file",
    "render_templates_with_filters",
    "resolve_env_variables",
    "validate_config",
    "__version__",
)
