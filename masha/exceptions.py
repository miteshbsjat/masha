"""
Custom exception hierarchy for MASHA.

This module defines the base exception and domain-specific exceptions
used throughout the application for graceful error handling.
"""


class MashaBaseError(Exception):
    """Base exception for all MASHA-specific errors."""


class ConfigLoadError(MashaBaseError):
    """Exception raised when a configuration file cannot be loaded."""


class ModelValidationError(MashaBaseError):
    """Exception raised when configuration fails Pydantic validation."""


class TemplateRenderError(MashaBaseError):
    """Exception raised when a Jinja2 template cannot be rendered."""
