import logging
import sys

from masha.logger_factory import (
    DEFAULT_FORMAT,
    configure_logging,
    create_logger,
)


def _cli_handlers() -> list[logging.Handler]:
    return [
        h
        for h in logging.getLogger("masha").handlers
        if h.get_name() == "masha-cli"
    ]


class TestConfigureLogging:
    def test_default_level_is_info(self):
        configure_logging()
        assert logging.getLogger("masha").level == logging.INFO

    def test_verbose_level_is_debug(self):
        configure_logging(verbose=True)
        assert logging.getLogger("masha").level == logging.DEBUG

    def test_idempotent_single_handler(self):
        configure_logging()
        configure_logging(verbose=True)
        configure_logging()
        assert len(_cli_handlers()) == 1
        assert logging.getLogger("masha").level == logging.INFO

    def test_logs_to_stderr_with_standard_format(self):
        configure_logging()
        (handler,) = _cli_handlers()
        assert isinstance(handler, logging.StreamHandler)
        assert handler.stream is sys.stderr
        assert handler.formatter is not None
        assert handler.formatter._fmt == DEFAULT_FORMAT

    def test_does_not_touch_root_logger(self):
        root = logging.getLogger()
        handlers_before = list(root.handlers)
        level_before = root.level
        configure_logging(verbose=True)
        assert root.handlers == handlers_before
        assert root.level == level_before
        assert logging.getLogger("masha").propagate is False

    def test_child_loggers_inherit_level(self):
        configure_logging(verbose=True)
        child = logging.getLogger("masha.config_loader")
        assert child.isEnabledFor(logging.DEBUG)


class TestCreateLogger:
    def test_returns_named_configured_logger(self):
        logger = create_logger("masha.something", verbose=True)
        assert logger.name == "masha.something"
        assert logger.isEnabledFor(logging.DEBUG)
        assert len(_cli_handlers()) == 1


class TestImportSideEffects:
    def test_importing_package_installs_no_handlers(self):
        import masha  # noqa: F401

        assert _cli_handlers() == []
